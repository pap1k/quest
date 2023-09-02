import config, telebot
from pending import Confirmation
from progress import Progress
from telebot import types
from script import Script, Line

bot = telebot.TeleBot(config.TOKEN)

scripts = [
    Script(config.script_file[0]),
    Script(config.script_file[1]),
    Script(config.script_file[2]),
    Script(config.script_file[3]),
    Script(config.script_file[4]),
]

name_to_script = {
    "jim hawkins": 0,
    "doctor livesey": 1,
    "john silver": 2,
    "captain smollett": 3,
    "robert louis stevenson": 4,
}

progress = Progress()

pending_requests: list[Confirmation] = []

markup_closed = types.InlineKeyboardMarkup()
markup_closed.add(types.InlineKeyboardButton("Обработано", callback_data="-"))

for script in scripts:
    if not script.status:
        print("=========================")
        print(f"Ошибка компиляции скрипта {script.filename}")
        for err in script.errors:
            print(err)
        quit()


def admin_announce(text):
    for admin in config.admins:
        bot.send_message(admin, text)


def send_admin_request__photo(message: types.Message):
    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton(
            "Принять", callback_data=f"accept:{message.from_user.id}"
        ),
        types.InlineKeyboardButton(
            "Отклонить", callback_data=f"deny:{message.from_user.id}"
        ),
    )
    conf = Confirmation(message.from_user.id)

    for admin in config.admins:
        conf.messages.append(
            bot.send_photo(
                admin,
                message.photo[-1].file_id,
                caption=f"Новое фото от @{message.from_user.username} ({message.from_user.id})",
                reply_markup=mk,
            )
        )

    pending_requests.append(conf)


def send_admin_request__video(message: types.Message):
    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton(
            "Принять", callback_data=f"accept:{message.from_user.id}"
        ),
        types.InlineKeyboardButton(
            "Отклонить", callback_data=f"deny:{message.from_user.id}"
        ),
    )
    conf = Confirmation(message.from_user.id)
    if message.video_note:
        for admin in config.admins:
            bot.send_video_note(admin, message.video_note.file_id)
            conf.messages.append(
                bot.send_message(
                    admin,
                    f"Новое видео от @{message.from_user.username} ({message.from_user.id})",
                    reply_markup=mk,
                )
            )
    elif message.video:
        for admin in config.admins:
            conf.messages.append(
                bot.send_video(
                    admin,
                    message.video.file_id,
                    caption=f"Новое видео от @{message.from_user.username} ({message.from_user.id})",
                    reply_markup=mk,
                )
            )

    pending_requests.append(conf)


def mega_send(uid, line: Line):
    for text in line.text:
        if text.startswith("--special_action"):
            action = text.replace("--special_action ", "")
            if action == "input":
                progress.get(uid).is_input = True
                progress.get(uid).compare_with = ""
            elif action == "photo_request":
                progress.get(uid).is_photo_requested = True
            elif action == "video_request":
                progress.get(uid).is_video_requested = True
            elif action == "end":
                progress.remove(progress.get(uid))
                admin_announce(f"Пользователь @{uid} прошел квест")
                return
            elif action.startswith("input_comp"):
                progress.get(uid).is_input = True
                progress.get(uid).compare_with = action.replace("input_comp ", "")
            else:
                admin_announce(
                    f"!!Ошибка определения специального действия у пользователя @{uid}"
                )
            progress.get(uid).line_n = line.id
            progress.do_backup()
        else:
            text = text.replace("---", "\n")
            bot.send_message(uid, text, parse_mode="HTML")


@bot.message_handler(["start"])
def new_message(message: types.Message):
    if progress.get(message.from_user.id):
        u = progress.get(message.from_user.id)
        u.is_input = False
        u.is_photo_requested = False
        u.is_video_requested = False
        u.line_n = 0
    else:
        u = progress.new(message.from_user.id)
    mega_send(message.from_user.id, scripts[u.script_id].get_line(u.line_n))
    admin_announce(
        f"Пользователь @{message.from_user.username} ({message.from_user.id}) запустил бота"
    )


@bot.callback_query_handler(lambda x: True)
def cb(cb: types.CallbackQuery):
    global pending_requests
    act = cb.data.split(":")[0]
    id = int(cb.data.split(":")[1])

    for conf in pending_requests:
        if conf.from_id == id:
            for mess in conf.messages:
                # bot.edit_message_reply_markup(
                #     mess.chat.id, mess.id, reply_markup=markup_closed
                # )
                if mess.text:
                    bot.edit_message_text("Обработано", mess.chat.id, mess.id)
                if mess.photo or mess.video:
                    bot.edit_message_caption("Обработано", mess.chat.id, mess.id)

    if act == "deny":
        bot.send_message(id, "Что-то на фото не так...")
    elif act == "accept":
        # bot.send_message(id, "Есть ответ! Двигаемся дальше...")
        u = progress.get(id)
        u.is_photo_requested = False
        u.is_video_requested = False
        data = scripts[u.script_id].get_line(u.line_n)
        mega_send(id, data)
    else:
        print("Ошибка определения экшена в колбеке")

    pending_requests = list(filter(lambda x: x.from_id != id, pending_requests))

    bot.answer_callback_query(cb.id, "Успешно")


@bot.message_handler(func=lambda v: True)
def just_message(message: types.Message):
    u = progress.get(message.from_user.id)
    if u:
        if u.is_input:
            if u.compare_with != "":
                try:
                    u.compare_with.index("|")
                    check = message.text.lower().strip() not in list(
                        map(str.strip, u.compare_with.lower().split("|"))
                    )
                except ValueError:
                    check = (
                        message.text.lower().strip() != u.compare_with.lower().strip()
                    )

                if check:
                    return bot.reply_to(
                        message, "Что-то тут не так... Попробуй еще раз повнимательнее"
                    )
                if u.line_n == 3:
                    u.script_id = name_to_script[message.text.lower().strip()]
                    admin_announce(
                        f"Участник @{message.from_user.username} ввел имя {message.text} и получил сценарий №{u.script_id+1}"
                    )
            u.is_input = False
            u.compare_with = ""
            data = scripts[u.script_id].get_line(u.line_n)
            mega_send(message.from_user.id, data)


@bot.message_handler(content_types=["photo"])
def new_photo(message: types.Message):
    u = progress.get(message.from_user.id)
    if u:
        if u.is_photo_requested:
            bot.reply_to(
                message,
                "Принял твое фото и отправил его матросам. Жди подтверждения",
            )
            send_admin_request__photo(message)
        else:
            bot.reply_to(message, "Я не жду от тебя фотографий.")


@bot.message_handler(content_types=["video", "video_note"])
def new_photo(message: types.Message):
    u = progress.get(message.from_user.id)
    if u:
        if u.is_video_requested:
            bot.reply_to(
                message,
                "Принял твое видео и отправил его матросам. Жди подтверждения",
            )
            send_admin_request__video(message)
        else:
            bot.reply_to(message, "Я не жду от тебя видео.")


bot.infinity_polling()
