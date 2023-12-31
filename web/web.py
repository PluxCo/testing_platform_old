import datetime
import json
import logging
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit

from data_accessors.auth_accessor import GroupsDAO, Group, PersonDAO
from data_accessors.questions_accessor import QuestionsDAO, Question, QuestionType, SettingsDAO as QuestionSettingsDAO, \
    Settings as QuestionSettings, StatisticsDAO, AnswerRecordDAO
from data_accessors.tg_accessor import SettingsDAO as TgSettingsDAO, Settings as TgSettings
from forms import CreateQuestionForm, ImportQuestionForm, EditQuestionForm, DeleteQuestionForm, CreateGroupForm, \
    TelegramSettingsForm, ScheduleSettingsForm, PausePersonForm, PlanQuestionForm
from utils import fusionauth_login_required

app = Flask(__name__)
socketio = SocketIO(app)

from fusionauth.fusionauth_client import FusionAuthClient

fusionauth_client = FusionAuthClient(api_key=os.getenv('FUSIONAUTH_CLIENT_ID'),
                                     base_url=os.getenv('FUSIONAUTH_DOMAIN'))


@app.route('/login')
def login():
    login_url = f"{fusionauth_client.base_url}/oauth2/authorize?client_id={fusionauth_client.api_key}&redirect_uri={url_for('callback', _external=True)}&response_type=code"
    return redirect(login_url)


@app.route('/logout')
def logout():
    user_id = session.pop('user_id', None)
    access_token = session.pop('access_token', None)

    if access_token:
        response = fusionauth_client.revoke_token(access_token)

    logout_url = f"{fusionauth_client.base_url}/oauth2/logout?client_id={fusionauth_client.api_key}"

    return redirect(logout_url)


@app.route('/callback')
def callback():
    # Extract the authorization code from the request
    code = request.args.get('code')

    # Exchange the authorization code for an access token
    response = fusionauth_client.exchange_o_auth_code_for_access_token(
        code,
        url_for('callback', _external=True),
        client_id=os.getenv('FUSIONAUTH_CLIENT_ID'),
        client_secret=os.getenv('FUSIONAUTH_CLIENT_SECRET')
    )
    print(response.status)
    # Extract user information from the FusionAuth response
    user_id = response.success_response['userId']
    print(user_id)

    # Store user_id in the session
    session['user_id'] = user_id

    # Redirect to the main page
    return redirect(url_for('main_page'))


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

    orders = ["id", "text", "subject", "options", "answer", "groups",
              "level", "article_url", "type"]

    cur_order = orders[int(args["order[0][column]"])]

    res["recordsTotal"] = len([q for q in QuestionsDAO.get_questions()])

    questions = [q for q in
                 QuestionsDAO.get_questions(args['search[value]'], cur_order, args["order[0][dir]"] != "asc")]

    res["recordsFiltered"] = len(questions)

    questions = questions[offset:offset + length]

    for q in questions:
        if q.options:
            options = "<ol>" + "".join(f"<li>{option}</li>" for option in q.options) + "</ol>"
        else:
            options = ""
        groups = []
        for g in q.groups:
            try:
                groups.append(GroupsDAO.get_group(g).label)
            except:
                logging.error(f"Unavailable group-id: {g}")
        groups = ", ".join(groups)
        res["data"].append((q.id, q.text, q.subject, options, q.answer, groups, q.level, q.article))

    return jsonify(res)


@app.route("/questions", methods=["POST", "GET"])
def questions_page():
    create_question_form = CreateQuestionForm()
    import_question_form = ImportQuestionForm()
    edit_question_form = EditQuestionForm()
    delete_question_form = DeleteQuestionForm()

    active_tab = "CREATE"

    groups = [(str(g.id), g.label) for g in GroupsDAO.get_all_groups()]
    create_question_form.groups.choices = groups
    import_question_form.groups.choices = groups
    edit_question_form.groups.choices = groups

    if create_question_form.create.data and create_question_form.validate():
        active_tab = "CREATE"

        selected_groups = [g_id for g_id in create_question_form.groups.data]
        options = create_question_form.options.data.splitlines()
        new_question = Question(q_id=-1,
                                text=create_question_form.text.data,
                                subject=create_question_form.subject.data,
                                options=options,
                                answer=create_question_form.answer.data,
                                groups=selected_groups,
                                level=create_question_form.level.data,
                                article=create_question_form.article.data,
                                q_type=QuestionType.OPEN if create_question_form.is_open.data else QuestionType.TEST)

        QuestionsDAO.create_question(new_question)

        create_question_form = CreateQuestionForm(formdata=None,
                                                  subject=create_question_form.subject.data,
                                                  article=create_question_form.article.data)
        create_question_form.groups.choices = groups

    if import_question_form.import_btn.data and import_question_form.validate():
        active_tab = "IMPORT"

        selected_groups = [g_id for g_id in import_question_form.groups.data]

        new_questions = []

        try:
            for record in json.loads(import_question_form.import_data.data):
                if record["answer"] not in record["options"]:
                    import_question_form.import_data.errors.append(
                        f"Answer '{record['answer']}' wasn't found in options")
                    break

                answer = record["options"].index(record["answer"]) + 1

                new_questions.append(Question(q_id=-1,
                                              text=record["question"],
                                              subject=import_question_form.subject.data,
                                              options=record["options"],
                                              groups=selected_groups,
                                              answer=answer,
                                              level=record["difficulty"],
                                              article=import_question_form.article.data,
                                              q_type=QuestionType.TEST))
            else:
                for question in new_questions:
                    QuestionsDAO.create_question(question)

                import_question_form = ImportQuestionForm(formdata=None,
                                                          groups=import_question_form.groups.data)
                import_question_form.groups.choices = groups
        except (json.decoder.JSONDecodeError, KeyError) as e:
            import_question_form.import_data.errors.append("Decode error: {}".format(e))

    if edit_question_form.save.data and edit_question_form.validate():
        question_id = int(edit_question_form.id.data)
        selected_groups = edit_question_form.groups.data

        question = Question(question_id,
                            edit_question_form.text.data,
                            edit_question_form.subject.data,
                            edit_question_form.options.data.splitlines(),
                            edit_question_form.answer.data,
                            selected_groups,
                            edit_question_form.level.data,
                            edit_question_form.article.data,
                            q_type=QuestionType.TEST)

        QuestionsDAO.update_question(question)

        return redirect("/questions")

    if delete_question_form.delete.data:
        QuestionsDAO.delete_question(int(delete_question_form.id.data))

        return redirect("/questions")

    return render_template("question.html",
                           active_tab=active_tab,
                           create_question_form=create_question_form,
                           import_question_form=import_question_form,
                           edit_question_form=edit_question_form,
                           delete_question_form=delete_question_form,
                           title="Questions")


@app.route("/settings", methods=["POST", "GET"])
@fusionauth_login_required
def settings_page():
    q_settings = QuestionSettingsDAO.get_settings()
    tg_settings = TgSettingsDAO.get_settings()

    create_group_form = CreateGroupForm()
    tg_settings_form = TelegramSettingsForm(tg_pin=tg_settings.pin)
    schedule_settings_form = ScheduleSettingsForm(time_period=q_settings.time_period, week_days=q_settings.week_days,
                                                  from_time=q_settings.from_time, to_time=q_settings.to_time)

    if create_group_form.create_group.data and create_group_form.validate():
        new_group = Group("", create_group_form.name.data)

        GroupsDAO.create_group(new_group)

        return redirect("/settings")

    if tg_settings_form.save_tg.data and tg_settings_form.validate():
        settings = TgSettings(tg_settings_form.tg_pin.data)

        TgSettingsDAO.update_settings(settings)
        return redirect("/settings")

    if schedule_settings_form.save_schedule.data and schedule_settings_form.validate():
        settings = QuestionSettings(schedule_settings_form.time_period.data, schedule_settings_form.from_time.data,
                                    schedule_settings_form.to_time.data, schedule_settings_form.week_days.data)

        QuestionSettingsDAO.update_settings(settings)
        return redirect("/settings")

    groups = GroupsDAO.get_all_groups()
    return render_template("settings.html", create_group_form=create_group_form, groups=groups,
                           schedule_settings_form=schedule_settings_form,
                           tg_settings_form=tg_settings_form,
                           title="Settings")


@app.route("/")
@fusionauth_login_required
def main_page():
    persons = PersonDAO.get_all_people()
    position_to_name = {}
    for i, person in enumerate(persons):
        position_to_name[i] = person.full_name
    return render_template("index.html", id_to_name=json.dumps(position_to_name, ensure_ascii=False), title="Tests")


@app.route("/statistic/<string:person_id>", methods=["POST", "GET"])
@fusionauth_login_required
def statistic_page(person_id):
    person = PersonDAO.get_person(person_id)

    pause_form = PausePersonForm()

    plan_form = PlanQuestionForm(ask_time=datetime.datetime.now(),
                                 person_id=person.id)

    timeline = []
    #
    # if pause_form.pause.data and pause_form.validate():
    #     person.is_paused = True
    #     db.commit()
    # if pause_form.unpause.data and pause_form.validate():
    #     person.is_paused = False
    #     db.commit()

    user_stats = StatisticsDAO.get_user_statistics(person_id)

    subject_stat = user_stats['subject_statistics']
    bar_data = user_stats['bar_data']

    if plan_form.plan.data and plan_form.validate():
        AnswerRecordDAO.plan_question(plan_form.question_id.data, plan_form.person_id.data, plan_form.ask_time.data)

    # for check_time in [datetime.datetime.now() + datetime.timedelta(x / 3) for x in range(-120, 1)]:
    #     correct_questions_amount = db.scalar(
    #         select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
    #                                                                    QuestionAnswer.answer_time <= check_time,
    #                                                                    QuestionAnswer.state == AnswerState.ANSWERED,
    #                                                                    Question.answer == QuestionAnswer.person_answer))
    #     incorrect_questions_amount = db.scalar(
    #         select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
    #                                                                    QuestionAnswer.answer_time <= check_time,
    #                                                                    QuestionAnswer.state == AnswerState.ANSWERED,
    #                                                                    Question.answer != QuestionAnswer.person_answer))
    #     ignored_questions_amount = db.scalar(
    #         select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
    #                                                                    QuestionAnswer.ask_time <= check_time,
    #                                                                    QuestionAnswer.state == AnswerState.TRANSFERRED,
    #                                                                    QuestionAnswer.person_answer == None))
    #
    #     timeline.append((check_time.timestamp() * 1000, correct_questions_amount, incorrect_questions_amount,
    #                      ignored_questions_amount))

    return render_template("statistic.html", person=person, subjects=subject_stat,
                           timeline=[], bar_data=json.dumps(bar_data, ensure_ascii=False),
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


@socketio.on('index_connected')
def people_list():
    persons = PersonDAO.get_all_people()
    short_stats = StatisticsDAO.get_short_statistics()
    for person in persons:
        emit('peopleList', {"person": {"id": person.id, "full_name": person.full_name},
                            **short_stats[person.id]})
        socketio.sleep(0)


@socketio.on('index_connected_timeline')
def timeline():
    persons = PersonDAO.get_all_people()
    timeline_correct = []
    timeline_incorrect = []
    id_to_position = {}
    for i, person in enumerate(persons):
        id_to_position[person.id] = i
    all_answers = AnswerRecordDAO.get_all_records()

    # TODO: Add open questions checking

    for answer in all_answers:
        if answer.answer_time:
            if answer.points:
                timeline_correct.append((answer.answer_time.timestamp() * 1000, id_to_position[answer.person_id], 5))
            else:
                timeline_incorrect.append((answer.answer_time.timestamp() * 1000, id_to_position[answer.person_id], 3))

    config = {
        "timeline_data_correct": [{"x": x, "y": y, "r": r} for x, y, r in timeline_correct],
        "timeline_data_incorrect": [{"x": x, "y": y, "r": r} for x, y, r in timeline_incorrect],
    }

    emit('timeline', json.dumps(config))


@socketio.on("get_question_stat")
def get_question_stat(data):
    res = StatisticsDAO.get_question_statistics(data["question_id"],
                                                data["person_id"] if "person_id" in data.keys() else "")
    emit("question_info", res)
