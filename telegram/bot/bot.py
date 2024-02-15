import datetime
import logging
import os
import random
import asyncio
from threading import Thread

import requests
import telebot
from requests import post, get
from sqlalchemy import select, or_
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from bot.models.telegram_types import MessageType, AnswerType, Person, SessionState, SimpleMessage, MessageWithButtons, \
    Motivation
from bot.models.response_types import SessionInfo, MessageInfo, MessageResponse, Webhook, Reply, Button
from bot.models.response_types import Message as AnswerMessageType

from models.db_session import create_session
from models.message import Message as MessageModel
from models.user import User
from models.sessions import Session
from tools import Settings

bot = telebot.TeleBot(os.environ["TG_TOKEN"])
people = dict()

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


@bot.callback_query_handler(func=lambda call: call.data.startswith("start") or call.data.startswith("end"))
def submit_buttons(call: CallbackQuery):
    if call.data == "start":
        message = bot.send_message(call.message.chat.id, "Введите код доступа")
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        bot.register_next_step_handler(message, password_check)

    elif call.data == "end_of_register":
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        target_level(call.message)


def target_level(message: Message):
    tg_id = message.chat.id
    groups = get(os.environ["FUSIONAUTH_DOMAIN"] + "/api/group",
                 headers={"Authorization": os.environ["FUSIONAUTH_TOKEN"]}).json()["groups"]

    if people[tg_id].groups:
        bot.send_message(tg_id, "Теперь нужно ввести уровень каждой выбранной вами группы(уровень - целое число)")
        bot.send_message(tg_id, [group for group in groups if group["id"] == people[tg_id].groups[0]][0]["name"])
        bot.register_next_step_handler(message, add_target_level)
    else:
        add_new_person(message)
        bot.send_message(tg_id, "Регистрация завершена. Теперь вам будут приходить вопросы в тестовой форме, "
                                "на которые нужно будет отвечать. Желаю удачи")


def add_target_level(message: Message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Неверный формат ввода, нужно ввести число. Попробуйте ещё раз")
    else:
        groups = get(os.environ["FUSIONAUTH_DOMAIN"] + "/api/group",
                     headers={"Authorization": os.environ["FUSIONAUTH_TOKEN"]}).json()["groups"]

        person = people[message.from_user.id]
        group_id = len(person.group_levels.keys())
        person.group_levels[person.groups[len(person.group_levels.keys())]] = int(message.text)
        if len(person.group_levels.keys()) < len(person.groups):
            bot.send_message(message.chat.id,
                             [group for group in groups if group["id"] == person.groups[group_id + 1]][0]["name"])
            bot.register_next_step_handler(message, add_target_level)
        else:
            add_new_person(message)
            bot.send_message(message.from_user.id,
                             "Регистрация завершена. Теперь вам будут приходить вопросы в тестовой форме, "
                             "на которые нужно будет отвечать. Желаю удачи")


def password_check(message: Message):
    with create_session() as db:
        if message.text == Settings()["pin"]:
            person_in_db = False
            user_tg_id = message.from_user.id
            if db.get(User, user_tg_id):
                person_in_db = True

            if not person_in_db:
                msg = bot.send_message(message.chat.id, 'Как тебя зовут(ФИО)?')
                bot.register_next_step_handler(msg, get_information_about_person)
            else:
                bot.send_message(message.chat.id, 'Рады Вас видеть вновь!')
                bot.send_sticker(message.chat.id, random.choice(stickers["is_registered"]))
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

        groups = get(os.environ["FUSIONAUTH_DOMAIN"] + "/api/group",
                     headers={"Authorization": os.environ["FUSIONAUTH_TOKEN"]}).json()

        for prof in groups["groups"]:
            profession_markup.add(InlineKeyboardButton(prof["name"], callback_data='group_' + prof["id"]))
        profession_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
        bot.send_message(message.from_user.id, 'Выбери группы, к которым ты относишься',
                         reply_markup=profession_markup)


def add_new_person(message: Message):
    person = people[message.from_user.id].to_json()

    try:
        r = post(os.environ["FUSIONAUTH_DOMAIN"] + "/api/user",
                 headers={"Authorization": os.environ["FUSIONAUTH_TOKEN"]},
                 json=person).json()
        people.pop(message.from_user.id)
        with create_session() as db:
            user = User()
            user.tg_id = message.from_user.id
            user.auth_id = r["user"]["id"]
            db.add(user)
            db.commit()
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('group'))
def select_groups(call: CallbackQuery):
    group_id = call.data.split('_')[1]
    person = people[call.from_user.id]
    groups = get(os.environ["FUSIONAUTH_DOMAIN"] + "/api/group",
                 headers={"Authorization": os.environ["FUSIONAUTH_TOKEN"]}).json()

    if group_id not in person.groups:
        person.groups.append(group_id)
    else:
        person.groups.remove(group_id)
    groups_markup = InlineKeyboardMarkup()

    for prof in groups["groups"]:

        if prof["id"] in person.groups:
            groups_markup.add(
                InlineKeyboardButton(prof["name"] + "\U00002713", callback_data='group_' + str(prof["id"])))
        else:
            groups_markup.add(InlineKeyboardButton(prof["name"], callback_data='group_' + str(prof["id"])))

    groups_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))

    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=groups_markup)


def send_messages(messages, webhook):
    # array of message_id of sending messages
    message_ids = []
    tg_ids = []
    user_fusion_ids = [message["user_id"] for message in messages]
    users_ids = {}
    with create_session() as db:
        current_users = db.scalars(select(User).where(User.auth_id.in_(user_fusion_ids)))
        for user in current_users:
            users_ids[user.auth_id] = user.tg_id
    for message in messages:

        user_id = message["user_id"]
        if str(user_id) not in users_ids.keys():
            message_ids.append(None)
            tg_ids.append(None)
            continue
        current_tg_id = users_ids[str(user_id)]

        tg_ids.append(current_tg_id)
        message_id = None

        # sending simple message
        if message["type"] == MessageType.SIMPLE.value:
            current_message = SimpleMessage(message)
            message_id = bot.send_message(int(current_tg_id), current_message.text).message_id


        # sending message with buttons
        elif message["type"] == MessageType.WITH_BUTTONS.value:
            current_message = MessageWithButtons(message)
            btn_group = InlineKeyboardMarkup()
            for btn_id in range(len(current_message.buttons)):
                btn_group.add(
                    InlineKeyboardButton(current_message.buttons[btn_id], callback_data="answer_" + str(btn_id)),
                    row_width=len(current_message.buttons))
            message_id = bot.send_message(int(current_tg_id), current_message.text,
                                          reply_markup=btn_group).message_id


        # sending motivation
        elif message["type"] == MessageType.MOTIVATION.value:
            current_message = Motivation(message)
            message_id = bot.send_sticker(int(current_tg_id),
                                          stickers["is_registered"][
                                              random.randint(0, len(stickers["is_registered"]) - 1)]).message_id

        message_ids.append(message_id)
    messages_info = []
    with create_session() as db:
        for i in range(len(message_ids)):
            current_session = db.scalar(select(Session).where(Session.user_tg_id == tg_ids[i],
                                                              or_(Session.session_state == SessionState.OPEN.value,
                                                                  Session.session_state == SessionState.PENDING.value)))

            if message_ids[i] is not None:
                if current_session:
                    current_session_id = current_session.id
                    current_session_state = current_session.session_state
                else:
                    new_session = Session(session_state=SessionState.PENDING.value,
                                          user_tg_id=int(tg_ids[i]),
                                          opening_time=datetime.datetime.now(),
                                          amount_of_questions=0)
                    db.add(new_session)
                    db.commit()
                    current_session_id = new_session.id
                    current_session_state = new_session.session_state
                current_fusion_id = db.get(User, tg_ids[i]).auth_id
                message_info = MessageInfo(int(message_ids[i]), SessionInfo(current_fusion_id, current_session_state))
            else:
                message_info = MessageInfo(None, SessionInfo(None, SessionState.CLOSE.value))

            messages_info.append(message_info)
            if message_ids[i] is not None:
                db.add(MessageModel(tg_id=int(tg_ids[i]),
                                    message_id=str(message_ids[i]),
                                    webhook=str(webhook),
                                    message_type=current_message.type,
                                    session_id=current_session_id))
                db.commit()
        response = MessageResponse(messages_info)
    return response


@bot.message_handler()
def get_answer(message: Message):
    if not message.reply_to_message:
        bot.send_message(message.from_user.id, "Чтобы дать ответ, ответьте на сообщение с вопросом")
        bot.send_sticker(message.from_user.id, random.choice(stickers["is_registered"]))
    else:

        with create_session() as db:
            current_question = db.scalar(
                select(MessageModel).where(MessageModel.message_id == message.reply_to_message.id,
                                           MessageModel.tg_id == message.from_user.id))
            current_session = db.scalar(select(Session).where(Session.id == current_question.session_id))

            if current_question:
                user = db.get(User, current_question.tg_id)
                user_answer = Reply(message.text, message.message_id, message.reply_to_message.id)

                if current_session:
                    current_session.amount_of_questions += 1
                    if current_session.session_state == SessionState.OPEN.value:
                        if ((datetime.datetime.now() - current_session.opening_time).total_seconds()
                                >= Settings()["session_duration"] or
                                current_session.amount_of_questions >= Settings()["amount_of_questions"]):
                            current_session.session_state = SessionState.CLOSE.value
                            session_info = SessionInfo(user.auth_id, SessionState.CLOSE.value)
                        else:
                            session_info = SessionInfo(user.auth_id, SessionState.OPEN.value)

                    elif current_session.session_state == SessionState.PENDING.value:
                        current_session.session_state = SessionState.OPEN.value
                        current_session.opening_time = datetime.datetime.now()
                        session_info = SessionInfo(user.auth_id, SessionState.OPEN.value)
                    else:
                        session_info = SessionInfo(user.auth_id, SessionState.CLOSE.value)

                    webhook = Webhook(user_answer, session_info)
                    webhook.post(current_question.webhook)
                else:
                    bot.send_message(message.from_user.id, "Извините, произошли технические шоколадки")
                    bot.send_sticker(message.from_user.id, stickers["wrong_answer"])

            else:
                bot.send_message(message.from_user.id, "Я Вас не понимаю :(")
            db.commit()


@bot.callback_query_handler(func=lambda call: call.data.startswith("answer"))
def handling_button_answers(call: CallbackQuery):
    button_id = int(call.data.split("_")[1])
    with create_session() as db:
        current_question = db.scalar(select(MessageModel).where(MessageModel.message_id == call.message.id,
                                                                MessageModel.tg_id == call.from_user.id))
        if current_question:
            current_session = db.scalar(select(Session).where(Session.id == current_question.session_id))
            webhook_from_db = current_question.webhook
            user = db.get(User, call.from_user.id)
            session_info = None
            if current_session:
                current_session.amount_of_questions += 1
                if current_session.session_state == SessionState.OPEN.value:
                    if ((datetime.datetime.now() - current_session.opening_time).total_seconds()
                            >= Settings()["session_duration"] or
                            current_session.amount_of_questions >= Settings()["amount_of_questions"]):

                        current_session.session_state = SessionState.CLOSE.value

                        session_info = SessionInfo(user.auth_id, SessionState.CLOSE.value)
                    else:
                        session_info = SessionInfo(user.auth_id, SessionState.OPEN.value)
                elif current_session.session_state == SessionState.PENDING.value:
                    current_session.session_state = SessionState.OPEN.value
                    current_session.opening_time = datetime.datetime.now()
                    session_info = SessionInfo(user.auth_id, SessionState.OPEN.value)
                else:
                    session_info = SessionInfo(user.auth_id, SessionState.CLOSE.value)
            else:
                bot.send_message(call.from_user.id, "Извините, произошли технические шоколадки")
                bot.send_sticker(call.from_user.id, stickers["wrong_answer"])
            user_answer = Button(button_id, call.message.id)
            logging.debug(f"user_answer: {user_answer.type}, {user_answer.__dict__}")
            webhook = Webhook(user_answer, session_info)
            response = webhook.post(webhook_from_db)
            if response:
                bot.edit_message_reply_markup(call.from_user.id, call.message.id)
            db.commit()


@bot.message_handler()
def strange_messages(message: Message):
    bot.send_message(message.from_user.id, "я не знаю такой команды")


def start_bot():
    bot_th = Thread(target=bot.infinity_polling, daemon=True)
    bot_th.start()
    return bot
