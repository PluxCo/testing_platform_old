import os

from flask import Flask, render_template, jsonify, request, redirect
from flask_socketio import SocketIO

from data_accessors.auth_accessor import GroupsDAO
from data_accessors.questions_accessor import QuestionsDAO, Question
from data_accessors.questions_accessor import SettingsDAO as QuestionSettingsDAO, Settings as QuestionSettings
from forms import CreateQuestionForm, ImportQuestionForm, EditQuestionForm, DeleteQuestionForm, CreateGroupForm, \
    TelegramSettingsForm, ScheduleSettingsForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

QuestionsDAO.set_host(os.getenv("QUESTIONS_URL", "http://localhost:3000"))
QuestionSettingsDAO.set_host(os.getenv("QUESTIONS_URL", "http://localhost:3000"))
GroupsDAO.set_host(os.getenv("FUSIONAUTH_HOST"), os.getenv("FUSIONAUTH_TOKEN"))


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

    # TODO: add sorting and limiting

    questions = list(QuestionsDAO.get_all_questions())

    res["recordsTotal"] = len(questions)

    res["recordsFiltered"] = len(questions)

    questions = questions[offset:offset + length]

    for q in questions:
        options = "<ol>" + "".join(f"<li>{option}</li>" for option in q.options) + "</ol>"
        groups = ", ".join(GroupsDAO.get_group(g).label for g in q.groups)
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
                                article=create_question_form.article.data)

        QuestionsDAO.create_question(new_question)

        create_question_form = CreateQuestionForm(formdata=None,
                                                  subject=create_question_form.subject.data,
                                                  article=create_question_form.article.data)
        create_question_form.groups.choices = groups

    return render_template("question.html",
                           active_tab=active_tab,
                           create_question_form=create_question_form,
                           import_question_form=import_question_form,
                           edit_question_form=edit_question_form,
                           delete_question_form=delete_question_form,
                           title="Questions")


@app.route("/settings", methods=["POST", "GET"])
def settings_page():
    create_group_form = CreateGroupForm()
    tg_settings_form = TelegramSettingsForm(data={})
    stg = QuestionSettingsDAO.get_settings()
    schedule_settings_form = ScheduleSettingsForm(time_period=stg.time_period, week_days=stg.week_days,
                                                  from_time=stg.from_time, to_time=stg.to_time)


    # if tg_settings_form.save_tg.data and tg_settings_form.validate():
    #     settings = tools.Settings()
    #     settings["tg_pin"] = tg_settings_form.tg_pin.data
    #
    #     settings.update_settings()
    #     return redirect("/settings")

    if schedule_settings_form.save_schedule.data and schedule_settings_form.validate():
        settings = QuestionSettings(schedule_settings_form.time_period.data, schedule_settings_form.from_time.data,
                                    schedule_settings_form.to_time.data, schedule_settings_form.week_days.data)

        QuestionSettingsDAO.update_settings(settings)
        return redirect("/settings")

    groups = []
    return render_template("settings.html", create_group_form=create_group_form, groups=groups,
                           schedule_settings_form=schedule_settings_form,
                           tg_settings_form=tg_settings_form,
                           title="Settings")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500


@app.errorhandler(401)
def login_error(e):
    return render_template('401.html'), 401


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", allow_unsafe_werkzeug=True, port=3002)
