import datetime
import json
import os
from threading import Thread

import telebot
from sqlalchemy import select
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from models import db_session
from models.questions import Question, QuestionAnswer, AnswerState
from models.users import Person, PersonGroup, PersonGroupAssociation
from tools import Settings
import random
from .generators import Session

bot = telebot.TeleBot(os.environ['TGTOKEN'])
people = dict()
target_levels = dict()
sessions = dict()
stickers = {"right_answer": ["CAACAgIAAxkBAAKlemTKcX143oNSqGVlHIjpmf5aWzRBAAJKFwACerrwSw3OVyhI-ZjLLwQ",
                             "CAACAgIAAxkBAAKmFWTKqiMrZzmS3yHPHN3nAAHUbElf3gACgRMAAvop0En6hsvCGJL_oy8E",
                             "CAACAgIAAxkBAAKlfGTKcYgpLL0FuHVCcRa_3cQBqnfJAAI0EgACEoP5S_q_MUdvvcoCLwQ",
                             "CAACAgIAAxkBAAKliGTKccWCj0_bLU0W6tV_ki-1xf1nAAJQFAACNX_ZSVKaub2cKslJLwQ",
                             "CAACAgIAAxkBAAKlkmTKcdxrsCohi6uqdA9mYfIL3H8HAAIiHQAC_spBS1V-vfQ_LslrLwQ",
                             "CAACAgIAAxkBAAKmEWTKqdm13n6k2GwYH-zdGQABXoz4bQAC3RgAApPBuEmJNu5i8B3Qiy8E",
                             "CAACAgIAAxkBAAKmJWTKqs5ELvVB6k_6ytKQYlVVwQUYAALhEQACpY3QSce04DLP8_LOLwQ",
                             "CAACAgIAAxkBAAKmJ2TKqt1ab7BNNdmETod0yvJkjqLEAALTFAAC66fQSVVyDz8ueKoYLwQ",
                             "CAACAgIAAxkBAAKllmTKcf0SFKClsR2U9g0wb3qO2TbIAAI2JAACk95BS5ci0XtsFrrHLwQ",
                             "CAACAgIAAxkBAAKmG2TKqmR17PHvROuTpdNXFgb4KQNVAAIhFwAC2MvQSW6hA3Ao-0wGLwQ",
                             "CAACAgIAAxkBAAKmEWTKqdm13n6k2GwYH-zdGQABXoz4bQAC3RgAApPBuEmJNu5i8B3Qiy8E",
                             "CAACAgIAAxkBAAKlmmTKchX8YZzr06N4WY61axvxjxMAA-sjAAI_5QFJd-WSKHcMUZMvBA"],
            "wrong_answer": ["CAACAgIAAxkBAAKlfmTKcY0cqGG0ohcLIzmRBl9h_PqUAAJwEgAC3qnwS3wgIciw53erLwQ",
                             "CAACAgIAAxkBAAKlgmTKcZtuRPIbFA-QSxy6QzuWospjAALAFwACSrFoSeIeiOZlqMJeLwQ",
                             "CAACAgIAAxkBAAKmI2TKqromehDnnmvfSASnhMTgJjTIAAISFQACe0bRSdV02GHIxIkOLwQ",
                             "CAACAgIAAxkBAAKmF2TKqkOczj8nzn0N_hmNBfVIkPWbAAIoFwACV8nRSaeLIyiBDmX6LwQ",
                             "CAACAgIAAxkBAAKlhmTKcb6V68c-7WIG8iLXUR6_WSgvAAIhFgACsYbRSR7B4XMTciBILwQ",
                             "CAACAgIAAxkBAAKmE2TKqfSFkgbLaDNbKvPLvyENua9xAAKrJgACMQtYSdkRj-6dgy0dLwQ",
                             "CAACAgIAAxkBAAKmIWTKqqBUmIhbkQVx7z-i4PS2a2UaAALBFgACCG3QSUKgWjqKlKvrLwQ",
                             "CAACAgIAAxkBAAKlimTKccuaj9BFKA9bkuRIHj2qSXTQAAJDEgACV6IwSTbcq4ACJlTALwQ",
                             "CAACAgIAAxkBAAKmGWTKqlVtbHg3EH5na-DuwRjhvkizAAKQFAAC6HrQSTCdZmRbJ4SkLwQ",
                             "CAACAgIAAxkBAAKljmTKcdSRkjGj70hVzCTSP5PDS1TaAAKUIgAC4DRASwQad8pJOZfILwQ",
                             "CAACAgIAAxkBAAKlkGTKcdf-kennRmE7M_GSTUNpksJ_AAIkHwACb39BS6qGc0muzL_lLwQ",
                             "CAACAgIAAxkBAAKlmGTKcgqcVQdm30vRVD4jiyp9hScYAAKcFgAC6055SNwcmwbagJ32LwQ"],
            "is_registered": ["CAACAgIAAxkBAAKlnGTKc0H-rDxgA6FM5lEgZKmkkjS_AALhFQACtEzYSdncM8HesAgILwQ",
                              "CAACAgIAAxkBAAKlnmTKc1hR_6CCFumJP-aEFzSVuiGRAAIBFQACfdZhSFpPzfo7g_TWLwQ",
                              "CAACAgIAAxkBAAKloGTKc3CSpCThXBGehxLykzDBmu4LAAL-EQACjoTwS6n-wbNdcuFALwQ",
                              "CAACAgIAAxkBAAKmH2TKqoUFNOK6dXkF9-35Oh_Lult9AAKuFQACO8LQSfxAhIpQexw9LwQ",
                              "CAACAgIAAxkBAAKlomTKc4iyNtpBVEc46HeqOI1oWExnAAJUFAACSYP4S6j1CfCFqLj9LwQ"]
            }


@bot.message_handler(commands=["start"])
def start_handler(message):
    start_markup = InlineKeyboardMarkup()
    start_markup.add(InlineKeyboardButton(text='Начать', callback_data='start'))
    bot.send_message(message.from_user.id,
                     'Привет, я бот для тестирования сотрудников 3divi. Перед началом тебе нужно ответить на пару '
                     'вопросов.', reply_markup=start_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('start') or call.data.startswith('end'))
def submit_buttons(call: CallbackQuery):
    if call.data == "start":
        message = bot.send_message(call.message.chat.id, 'Введите код доступа')
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        bot.register_next_step_handler(message, password_check)

    elif call.data == 'end_of_register':
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        add_new_person(call)


def target_level(message: Message):
    tg_id = message.chat.id

    if list(people[tg_id].groups):
        bot.send_message(tg_id, "Теперь нужно ввести уровень каждой выбранной вами группы(уровень - целое число)")
        bot.send_message(tg_id, list(people[tg_id].groups)[0].name)
        target_levels[tg_id] = []
    else:
        bot.send_message(tg_id, "Регистрация завершена. Теперь вам будут приходить вопросы в тестовой форме, "
                                "на которые нужно будет отвечать. Желаю удачи")


@bot.message_handler()
def add_target_level(message: Message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Неверный формат ввода, нужно ввести число. Попробуйте ещё раз")
    else:
        with db_session.create_session():
            target_levels[message.chat.id].append(int(message.text))
            if len(target_levels[message.chat.id]) < len(people[message.chat.id].groups):
                bot.send_message(message.chat.id, people[message.chat.id].groups[len(target_levels[message.chat.id])].
                                 name)
            else:
                update_target_levels(message)


def update_target_levels(message: Message):
    tg_id = message.chat.id
    with db_session.create_session() as db:
        for group in range(len(target_levels[tg_id])):
            level = db.scalar(select(PersonGroupAssociation).where(PersonGroupAssociation.person_id == people[tg_id].id)
                              .where(PersonGroupAssociation.group_id == people[tg_id].groups[group].id))
            level.target_level = target_levels[tg_id][group]
            db.commit()
    bot.send_message(tg_id, "Регистрация завершена. Теперь вам будут приходить вопросы в тестовой форме, "
                            "на которые нужно будет отвечать. Желаю удачи")


def password_check(message: Message):
    if message.text == Settings()["tg_pin"]:
        person_in_db = False
        with db_session.create_session() as db:
            if db.scalar(select(Person).where(Person.tg_id == message.chat.id)):
                person_in_db = True
        if not person_in_db:
            msg = bot.send_message(message.chat.id, 'Как тебя зовут(ФИО)?')
            bot.register_next_step_handler(msg, get_information_about_person)
        else:
            bot.send_message(message.chat.id, 'Вы уже зарегестрированы.')
            bot.send_sticker(message.chat.id,
                             stickers["is_registered"][random.randint(0, len(stickers["is_registered"]) - 1)])
    else:
        msg = bot.send_message(message.chat.id, 'Неверный код доступа. Попробуйте ещё раз.')
        bot.register_next_step_handler(msg, password_check)


def get_information_about_person(message: Message):
    full_name = message.text

    if len(full_name.split()) < 3:
        bot.send_message(message.from_user.id,
                         'Неправильный формат ввода. Обратите внимание на то, что нужно ввести Фамилию Имя Отчество. '
                         'Попробуйте ввести ещё раз.')
        bot.register_next_step_handler(message, get_information_about_person)
    else:
        people[message.from_user.id] = Person()
        people[message.from_user.id].full_name = full_name
        profession_markup = InlineKeyboardMarkup()

        with db_session.create_session() as db:

            for prof in db.scalars(select(PersonGroup)):
                profession_markup.add(InlineKeyboardButton(prof.name, callback_data='group_' + str(prof.id)))
            profession_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
            bot.send_message(message.from_user.id, 'Выбери группы, к которым ты относишься',
                             reply_markup=profession_markup)


def add_new_person(call: CallbackQuery):
    telegram_id = call.from_user.id
    people[telegram_id].tg_id = telegram_id
    with db_session.create_session() as db:
        db.add(people[telegram_id])
        db.commit()
        target_level(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('group'))
def select_groups(call: CallbackQuery):
    with db_session.create_session() as db:

        group_id = int(call.data.split('_')[1])
        groups = db.scalars(select(PersonGroup))
        person = people[call.from_user.id]
        current_group = db.scalars(select(PersonGroup).where(PersonGroup.id == group_id)).first()

        if current_group.id not in [group.id for group in person.groups]:
            person.groups.append(current_group)
        else:
            person.groups.remove([group for group in person.groups if group.id == group_id][0])
        groups_markup = InlineKeyboardMarkup()

        for prof in groups:
            if prof.id in [i.id for i in person.groups]:
                groups_markup.add(InlineKeyboardButton(prof.name + "\U00002713", callback_data='group_' + str(prof.id)))
            else:
                groups_markup.add(InlineKeyboardButton(prof.name, callback_data='group_' + str(prof.id)))

        groups_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=groups_markup)


# первыйй ответ дня, пять правильых ответов подряд ачивкки


def create_session(person: Person):
    session = Session(person, Settings()["max_time"], Settings()["max_questions"])
    sessions[person.tg_id] = session
    session.generate_questions()
    send_question(person)


def send_question(person: Person):
    answer = sessions[person.tg_id].next_question()
    if answer:
        with db_session.create_session() as db:
            answer = db.merge(answer)

            answer.state = AnswerState.TRANSFERRED
            db.commit()

            markup = InlineKeyboardMarkup()
            options = json.loads(answer.question.options)
            question_text = answer.question.text

        buttons = []
        for answer_index in range(len(options)):
            question_text += '\n' + str(answer_index + 1) + '. ' + options[answer_index]
            buttons.append(InlineKeyboardButton(answer_index + 1, callback_data='answer_' + str(answer.id) + '_' +
                                                                                str(answer_index + 1)))
        markup.add(*buttons, InlineKeyboardButton('Не знаю:(', callback_data='answer_' + str(answer.id) + '_0', ),
                   row_width=len(buttons))

        try:
            bot.send_message(person.tg_id, question_text, reply_markup=markup)
        except Exception as e:
            pass
    else:
        bot.send_message(person.tg_id, "Ты умничка, увидимся позже;)")


@bot.callback_query_handler(func=lambda call: call.data.startswith('answer'))
def check_answer(call: CallbackQuery):
    with db_session.create_session() as db:
        _, answer_id, answer_number = call.data.split('_')
        cur_answer = db.get(QuestionAnswer, int(answer_id))

        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        if answer_number == str(cur_answer.question.answer):
            bot.reply_to(call.message, 'Юхуууу, правильный ответ, ты умнииичка')
            bot.send_sticker(call.message.chat.id,
                             stickers["right_answer"][random.randint(0, len(stickers['right_answer']) - 1)])
        else:
            if cur_answer.question.article_url:
                bot.reply_to(call.message,
                             'Как жаль, ответ неправильный. Правильный ответ - \"'
                             + json.loads(cur_answer.question.options)[cur_answer.question.answer - 1]
                             + '\". Вот тебе интересная статья по этой теме.'
                             + '\n' + cur_answer.question.article_url)
                bot.send_sticker(call.from_user.id,
                                 stickers["wrong_answer"][random.randint(0, len(stickers['wrong_answer']) - 1)])
            else:
                bot.reply_to(call.message, 'Увы, ответ неправильный, не грустите. '
                                           'Правильный ответ \"' + json.loads(cur_answer.question.options)
                             [cur_answer.question.answer - 1] + "\"")
                bot.send_sticker(call.from_user.id,
                                 stickers["wrong_answer"][random.randint(0, len(stickers['wrong_answer']) - 1)])

        if cur_answer is not None:
            cur_answer.person_answer = int(answer_number)
            cur_answer.state = AnswerState.ANSWERED
            cur_answer.answer_time = datetime.datetime.now()
            db.commit()

        person = db.scalar(select(Person).where(Person.tg_id == call.from_user.id))
        send_question(person)


def start_bot():
    bot_th = Thread(target=bot.infinity_polling, daemon=True)
    bot_th.start()
    return bot
