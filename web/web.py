import datetime
import json
import os
import time

from flask import Flask, redirect, render_template, jsonify, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from sqlalchemy import select, func, distinct, or_

import tools
from models import db_session
from models.questions import QuestionAnswer, Question, AnswerState
from models.users import Person, PersonGroup

from web.forms.users import LoginForm, UserCork, CreateGroupForm, PausePersonForm
from web.forms.questions import CreateQuestionForm, ImportQuestionForm, PlanQuestionForm, EditQuestionForm, \
    DeleteQuestionForm
from web.forms.settings import TelegramSettingsForm, ScheduleSettingsForm, SessionSettingsForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return UserCork()


@app.route("/login", methods=["POST", "GET"])
def login_page():
    login_form = LoginForm()
    error = None

    if login_form.validate_on_submit():
        if login_form.passwd.data == os.environ.get("ADMIN_PASSWD"):
            login_user(UserCork())
            return redirect("/")
        else:
            error = "Incorrect password"

    return render_template("login.html", form=login_form, error_msg=error, title="Login")


@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout_page():
    logout_user()
    return redirect('/login')


@app.route("/")
def main_page():
    if not current_user.is_authenticated:
        return redirect("/login")
    with db_session.create_session() as db:
        persons = db.scalars(select(Person)).all()
        id_to_name = {}
        for person in persons:
            id_to_name[person.id] = person.full_name

    return render_template("index.html", id_to_name=json.dumps(id_to_name, ensure_ascii=False), title="Tests")


# noinspection PyTypeChecker
@app.route("/statistic/<int:person_id>", methods=["POST", "GET"])
@login_required
def statistic_page(person_id):
    with db_session.create_session() as db:
        pause_form = PausePersonForm()
        person = db.get(Person, person_id)

        plan_form = PlanQuestionForm(ask_time=datetime.datetime.now(),
                                     person_id=person.id)

        person_subjects = db.scalars(select(distinct(Question.subject)).join(Question.groups).
                                     where(PersonGroup.id.in_(pg.id for pg in person.groups)))
        subject_stat = []
        bar_stat = [[], [], []]
        timeline = []

        if pause_form.pause.data and pause_form.validate():
            person.is_paused = True
            db.commit()
        if pause_form.unpause.data and pause_form.validate():
            person.is_paused = False
            db.commit()

        if plan_form.plan.data and plan_form.validate():
            new_answer = QuestionAnswer(person_id=plan_form.person_id.data,
                                        question_id=plan_form.question_id.data,
                                        ask_time=plan_form.ask_time.data,
                                        state=AnswerState.NOT_ANSWERED)

            db.add(new_answer)
            db.commit()

        for name in person_subjects:
            all_questions = db.scalars(select(Question).
                                       join(Question.groups).
                                       where(Question.subject == name,
                                             PersonGroup.id.in_(pg.id for pg in person.groups)).
                                       group_by(Question.id)).all()

            correct_count = 0
            correct_count_by_level = {}
            answered_count = 0
            answered_count_by_level = {}
            questions_count = len(all_questions)
            person_answers = []

            for current_question in all_questions:
                answers = db.scalars(select(QuestionAnswer).
                                     where(QuestionAnswer.person_id == person.id,
                                           QuestionAnswer.question_id == current_question.id,
                                           QuestionAnswer.state != AnswerState.NOT_ANSWERED).
                                     order_by(QuestionAnswer.ask_time)).all()

                question_correct_count = len([1 for a in answers if a.person_answer == current_question.answer])
                question_incorrect_count = len(answers) - question_correct_count

                answer_state = "NOT_ANSWERED"
                if answers:
                    answered_count += 1

                    if answers[-1].question.level not in answered_count_by_level.keys():
                        answered_count_by_level[answers[-1].question.level] = 0
                        correct_count_by_level[answers[-1].question.level] = 0

                    answered_count_by_level[answers[-1].question.level] += 1

                    if answers[-1].state == AnswerState.TRANSFERRED:
                        answer_state = "IGNORED"
                    elif answers[-1].question.answer == answers[-1].person_answer:
                        correct_count += 1
                        correct_count_by_level[answers[-1].question.level] += 1
                        answer_state = "CORRECT"
                    else:
                        answer_state = "INCORRECT"

                person_answers.append((current_question, answer_state,
                                       question_correct_count, question_incorrect_count))

            subject_stat.append((name, correct_count, answered_count, questions_count, person_answers))
            progress_by_level = {}

            for level in answered_count_by_level:
                progress_by_level[level] = round(correct_count_by_level[level] / answered_count_by_level[level] * 100,
                                                 1)

            bar_stat[0].append(name)
            bar_stat[1].append(progress_by_level)
            if progress_by_level:
                bar_stat[2].append(max(progress_by_level, key=progress_by_level.get))
        if bar_stat[2]:
            max_level = max(bar_stat[2])
        else:
            max_level = 0
        progress_by_level = []
        for i in range(0, max_level):
            progress_by_level.append([])
            for j in range(len(bar_stat[1])):
                if (i + 1) in bar_stat[1][j].keys():
                    progress_by_level[i].append(bar_stat[1][j][i + 1])
                else:
                    progress_by_level[i].append(0)

        bar_data = [bar_stat[0], progress_by_level, max_level]
        for check_time in [datetime.datetime.now() + datetime.timedelta(x / 3) for x in range(-120, 1)]:
            correct_questions_amount = db.scalar(
                select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
                                                                           QuestionAnswer.answer_time <= check_time,
                                                                           QuestionAnswer.state == AnswerState.ANSWERED,
                                                                           Question.answer == QuestionAnswer.person_answer))
            incorrect_questions_amount = db.scalar(
                select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
                                                                           QuestionAnswer.answer_time <= check_time,
                                                                           QuestionAnswer.state == AnswerState.ANSWERED,
                                                                           Question.answer != QuestionAnswer.person_answer))
            ignored_questions_amount = db.scalar(
                select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
                                                                           QuestionAnswer.ask_time <= check_time,
                                                                           QuestionAnswer.state == AnswerState.TRANSFERRED,
                                                                           QuestionAnswer.person_answer == None))

            timeline.append((check_time.timestamp() * 1000, correct_questions_amount, incorrect_questions_amount,
                             ignored_questions_amount))

        return render_template("statistic.html", person=person,
                               AnswerState=AnswerState, subjects=subject_stat,
                               timeline=timeline, bar_data=json.dumps(bar_data, ensure_ascii=False),
                               pause_form=pause_form, plan_form=plan_form, title="Statistics: " + person.full_name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@app.errorhandler(401)
def login_error(e):
    return render_template('401.html'), 401

@socketio.on("get_question_stat")
def get_question_stat(data):
    with db_session.create_session() as db:
        res = {"question": None, "answers": []}

        question = db.get(Question, data["question_id"])
        res["question"] = question.to_dict(
            only=("text", "level", "groups.name", "answer", "id", "groups.id", "subject", "article_url"))
        res["question"]["options"] = json.loads(question.options)

        if "person_id" in data:
            answers = db.scalars(select(QuestionAnswer).
                                 where(QuestionAnswer.person_id == data["person_id"],
                                       QuestionAnswer.question_id == data["question_id"]).
                                 order_by(QuestionAnswer.ask_time))

            for a in answers:
                a: QuestionAnswer
                if a.state == AnswerState.TRANSFERRED:
                    answer_state = "IGNORED"
                elif a.state == AnswerState.NOT_ANSWERED:
                    answer_state = "NOT_ANSWERED"
                elif a.question.answer == a.person_answer:
                    answer_state = "CORRECT"
                else:
                    answer_state = "INCORRECT"

                res["answers"].append(a.to_dict(only=("person_answer", "answer_time", "ask_time")))
                res["answers"][-1]["state"] = answer_state

    emit("question_info", res)


@app.route("/questions_ajax")
def questions_ajax():
    args = request.args
    res = {
        "draw": args["draw"],
        "recordsTotal": 0,
        "recordsFiltered": 0,
        "data": []
    }

    length = int(args["length"])
    offset = int(args["start"])

    orders = [Question.id, Question.text, Question.subject, Question.options, Question.answer, Question.id,
              Question.level, Question.article_url]

    cur_order = orders[int(args["order[0][column]"])]
    if args["order[0][dir]"] != "asc":
        cur_order = cur_order.desc()

    with db_session.create_session() as db:
        res["recordsTotal"] = db.scalar(func.count(Question.id))

        questions = db.scalars(select(Question).
                               where(or_(Question.text.ilike(f"%{args['search[value]']}%"),
                                         Question.subject.ilike(f"%{args['search[value]']}%"),
                                         Question.options.ilike(f"%{args['search[value]']}%"),
                                         Question.level.ilike(f"%{args['search[value]']}%"),
                                         Question.article_url.ilike(f"%{args['search[value]']}%"))).
                               order_by(cur_order)).all()

        res["recordsFiltered"] = len(questions)

        if offset + length < len(questions):
            questions = questions[offset:offset + length]
        else:
            questions = questions[offset:]

        for q in questions:
            q: Question
            options = "<ol>" + "".join(f"<li>{option}</li>" for option in json.loads(q.options)) + "</ol>"
            groups = ", ".join(g.name for g in q.groups)
            res["data"].append((q.id, q.text, q.subject, options, q.answer, groups, q.level, q.article_url))

    return jsonify(res)


@app.route("/questions", methods=["POST", "GET"])
@login_required
def questions_page():
    with db_session.create_session() as db:
        create_question_form = CreateQuestionForm()
        import_question_form = ImportQuestionForm()
        edit_question_form = EditQuestionForm()
        delete_question_form = DeleteQuestionForm()

        active_tab = "CREATE"

        groups = [(str(item.id), item.name) for item in db.scalars(select(PersonGroup))]
        create_question_form.groups.choices = groups
        import_question_form.groups.choices = groups
        edit_question_form.groups.choices = groups

        if create_question_form.create.data and create_question_form.validate():
            active_tab = "CREATE"

            selected = [int(item) for item in create_question_form.groups.data]
            selected_groups = db.scalars(select(PersonGroup).where(PersonGroup.id.in_(selected)))
            options = json.dumps(create_question_form.options.data.splitlines(), ensure_ascii=False)
            new_question = Question(text=create_question_form.text.data,
                                    subject=create_question_form.subject.data,
                                    options=options,
                                    answer=create_question_form.answer.data,
                                    level=create_question_form.level.data,
                                    article_url=create_question_form.article.data)

            new_question.groups.extend(selected_groups)
            db.add(new_question)
            db.commit()

            create_question_form = CreateQuestionForm(formdata=None,
                                                      subject=create_question_form.subject.data,
                                                      article=create_question_form.article.data)
            create_question_form.groups.choices = groups

        if import_question_form.import_btn.data and import_question_form.validate():
            active_tab = "IMPORT"

            selected = [int(item) for item in import_question_form.groups.data]
            selected_groups = db.scalars(select(PersonGroup).where(PersonGroup.id.in_(selected))).all()

            try:
                for record in json.loads(import_question_form.import_data.data):
                    if record["answer"] not in record["options"]:
                        import_question_form.import_data.errors.append(
                            "Answer '{}' wasn't found in options".format(record["answer"]))
                        db.rollback()
                        break

                    answer = record["options"].index(record["answer"]) + 1

                    new_question = Question(text=record["question"],
                                            subject=import_question_form.subject.data,
                                            options=json.dumps(record["options"], ensure_ascii=False),
                                            answer=answer,
                                            level=record["difficulty"],
                                            article_url=import_question_form.article.data)
                    new_question.groups.extend(selected_groups)
                    db.add(new_question)
                else:
                    db.commit()

                    import_question_form = ImportQuestionForm(formdata=None,
                                                              groups=import_question_form.groups.data)
                    import_question_form.groups.choices = groups
            except (json.decoder.JSONDecodeError, KeyError) as e:
                import_question_form.import_data.errors.append(
                    "Decode error: {}".format(e))
                db.rollback()

        if edit_question_form.save.data and edit_question_form.validate():
            question_id = int(edit_question_form.id.data)
            selected = [int(item) for item in edit_question_form.groups.data]
            selected_groups = db.scalars(select(PersonGroup).where(PersonGroup.id.in_(selected))).all()

            question = db.get(Question, question_id)
            question.text = edit_question_form.text.data
            question.subject = edit_question_form.subject.data
            question.options = json.dumps(edit_question_form.options.data.splitlines(), ensure_ascii=False)
            question.answer = edit_question_form.answer.data
            question.level = edit_question_form.level.data
            question.article_url = edit_question_form.article.data
            question.groups[:] = []
            question.groups.extend(selected_groups)

            db.commit()

            return redirect("/questions")

        if delete_question_form.delete.data:
            question = db.get(Question, int(delete_question_form.id.data))
            db.delete(question)
            db.commit()

            return redirect("/questions")

        return render_template("question.html",
                               active_tab=active_tab,
                               create_question_form=create_question_form,
                               import_question_form=import_question_form,
                               edit_question_form=edit_question_form,
                               delete_question_form=delete_question_form,
                               title="Questions")


@app.route("/settings", methods=["POST", "GET"])
@login_required
def settings_page():
    db = db_session.create_session()
    create_group_form = CreateGroupForm()
    tg_settings_form = TelegramSettingsForm(data=tools.Settings())
    schedule_settings_form = ScheduleSettingsForm(data=tools.Settings(),
                                                  week_days=[d.value for d in tools.Settings()["week_days"]])
    session_settings_form = SessionSettingsForm(data=tools.Settings())

    if create_group_form.create_group.data and create_group_form.validate():
        new_group = PersonGroup()
        new_group.name = create_group_form.name.data
        db.add(new_group)
        db.commit()

        return redirect("/settings")

    if tg_settings_form.save_tg.data and tg_settings_form.validate():
        settings = tools.Settings()
        settings["tg_pin"] = tg_settings_form.tg_pin.data

        settings.update_settings()
        return redirect("/settings")

    if schedule_settings_form.save_schedule.data and schedule_settings_form.validate():
        settings = tools.Settings()
        settings["time_period"] = schedule_settings_form.time_period.data
        settings["week_days"] = [tools.WeekDays(d) for d in schedule_settings_form.week_days.data]
        settings["from_time"] = schedule_settings_form.from_time.data
        settings["to_time"] = schedule_settings_form.to_time.data

        settings.update_settings()
        return redirect("/settings")

    if session_settings_form.save_session_settings.data and session_settings_form.validate_on_submit():
        settings = tools.Settings()
        settings["max_time"] = session_settings_form.max_time.data
        settings["max_questions"] = session_settings_form.max_questions.data

        settings.update_settings()
        return redirect("/settings")

    groups = db.scalars(select(PersonGroup))
    return render_template("settings.html", create_group_form=create_group_form, groups=groups,
                           schedule_settings_form=schedule_settings_form,
                           tg_settings_form=tg_settings_form, session_settings_form=session_settings_form,
                           title="Settings")


@socketio.on('index_connected')
def people_list():
    with db_session.create_session() as db:
        persons = db.scalars(select(Person)).all()
        for person in persons:
            all_questions = db.scalars(select(Question).
                                       join(Question.groups).
                                       where(PersonGroup.id.in_(pg.id for pg in person.groups)).
                                       group_by(Question.id)).all()
            correct_count = 0
            answered_count = 0
            questions_count = len(all_questions)

            for current_question in all_questions:
                answers = db.scalars(select(QuestionAnswer).
                                     where(QuestionAnswer.person_id == person.id,
                                           QuestionAnswer.question_id == current_question.id,
                                           QuestionAnswer.state != AnswerState.NOT_ANSWERED).
                                     order_by(QuestionAnswer.ask_time)).all()

                if answers:
                    answered_count += 1
                    if answers[-1].question.answer == answers[-1].person_answer:
                        correct_count += 1

            emit('peopleList', json.dumps(
                {"person": {"id": person.id, "full_name": person.full_name},
                 "correct_count": correct_count,
                 "answered_count": answered_count,
                 "questions_count": questions_count},
                ensure_ascii=False))
            socketio.sleep(0)


@socketio.on('index_connected_timeline')
def timeline():
    with db_session.create_session() as db:
        persons = db.scalars(select(Person)).all()
        timeline_correct = []
        timeline_incorrect = []
        id_to_name = {}
        for person in persons:
            id_to_name[person.id] = person.full_name

        all_correct_answers = db.scalars(
            select(QuestionAnswer).join(Question).where(QuestionAnswer.person_answer == Question.answer)).all()
        all_incorrect_answers = db.scalars(
            select(QuestionAnswer).join(Question).where(QuestionAnswer.person_answer != Question.answer)).all()

        for answer in all_correct_answers:
            timeline_correct.append((answer.answer_time.timestamp() * 1000, answer.person_id, 5))
        for answer in all_incorrect_answers:
            timeline_incorrect.append((answer.answer_time.timestamp() * 1000, answer.person_id, 3))

        config = {
            "timeline_data_correct": [{"x": x, "y": y, "r": r} for x, y, r in timeline_correct],
            "timeline_data_incorrect": [{"x": x, "y": y, "r": r} for x, y, r in timeline_incorrect],
        }
        emit('timeline', json.dumps(config))
