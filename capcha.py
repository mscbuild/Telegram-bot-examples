import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    ChatPermissions,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# --- Конфигурация ---
TOKEN = "8098160840:AAFtH0mGJ4yy7RTHmScALd6c66vq_KWIbxw"
log_channel_id = -1002509686305  # Замените на ID вашего лог-канала
max_messages = 5
per_seconds = 10
CAPTCHA_ANSWER = "август"

# --- Хранение данных ---
user_langs = {}  # user_id -> 'ru' или 'en'
user_messages = defaultdict(list)  # user_id -> list[float(timestamp)]
warnings = defaultdict(lambda: {"count": 0})
pending_captcha = {}  # user_id -> chat_id

# --- Языковые словари ---
LANGS = {
    "ru": {
        "captcha_prompt": "Пожалуйста, докажите, что вы не бот.\nВведите слово 'август' для подтверждения.",
        "captcha_passed": "✅ Спасибо! Вы успешно прошли проверку.",
        "captcha_failed": "❌ Неверный ответ. Попробуйте еще раз.",
        "captcha_kick": "Пользователь {0} не прошел капчу и был исключен.",
    },
    "en": {
        "captcha_prompt": "Please prove you are not a bot.\nType the word 'август' to confirm.",
        "captcha_passed": "✅ Thank you! You passed the verification.",
        "captcha_failed": "❌ Wrong answer. Please try again.",
        "captcha_kick": "User {0} failed the captcha and was removed.",
    },
}

DELETE_BUTTONS_DELAY = 7 * 60  # 7 минут


# --- Вспомогательные функции ---

def get_lang(update: Update) -> str:
    user_id = update.effective_user.id
    return user_langs.get(user_id, "en")


async def is_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]


async def delete_message_later(bot, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass  # Сообщение удалено или нет прав


async def send_captcha(chat_id, user_id, member, context: ContextTypes.DEFAULT_TYPE):
    lang = user_langs.get(user_id, "en")
    t = LANGS[lang]

    await context.bot.send_message(
        chat_id=chat_id,
        text=t["captcha_prompt"],
    )

    pending_captcha[user_id] = chat_id

    await asyncio.sleep(60)

    if user_id in pending_captcha:
        # Не прошёл капчу — бан и разбан (кик)
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)
        del pending_captcha[user_id]
        await context.bot.send_message(
            chat_id,
            text=t["captcha_kick"].format(member.first_name),
        )


# --- Обработчики команд ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Показываем меню выбора языка
    await set_lang(update, context)


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите язык / Choose a language:", reply_markup=reply_markup)


# --- Обработчик выбора языка кнопками ---

async def on_lang_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data.startswith("set_lang_"):
        # Выбор языка из команды /lang или /start
        lang = query.data.split("_")[2]
        user_langs[user_id] = lang
        await query.edit_message_text(
            "✅ Язык установлен на русский." if lang == "ru" else "✅ Language set to English."
        )

    elif query.data.startswith("join_lang_"):
        # Выбор языка при входе в группу
        lang_code, chat_id_str = query.data.split(":")[0].split("_")[-1], query.data.split(":")[1]
        chat_id = int(chat_id_str)
        user_langs[user_id] = lang_code
        await query.edit_message_text(
            "✅ Язык установлен на русский." if lang_code == "ru" else "✅ Language set to English."
        )

        member = query.from_user
        await send_captcha(chat_id, user_id, member, context)


# --- Обработчик новых участников / входов в группу ---

async def on_user_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member.user
    chat_id = update.chat_member.chat.id
    user_id = member.id

    # Ограничиваем права, чтобы не флудил
    await context.bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
    )

    # Если язык не выбран — предлагаем выбор
    if user_id not in user_langs:
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data=f"join_lang_ru:{chat_id}"),
                InlineKeyboardButton("🇬🇧 English", callback_data=f"join_lang_en:{chat_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"{member.first_name}, выберите язык / choose your language:",
            reply_markup=reply_markup,
        )

        # Запускаем авто-удаление кнопок через 7 минут
        asyncio.create_task(delete_message_later(context.bot, chat_id, sent_msg.message_id, DELETE_BUTTONS_DELAY))
    else:
        # Если язык выбран — сразу капча
        await send_captcha(chat_id, user_id, member, context)


# --- Основной обработчик сообщений ---

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message = update.message

    if message is None:
        return  # Без сообщения (например, только событие)

    text = message.text.lower().strip() if message.text else ""

    lang = get_lang(update)
    t = LANGS[lang]
    now = time.time()

    # Игнорируем админов
    if await is_admin(chat_id, user_id, context):
        return

    # Проверяем, не в муте ли пользователь (у нас теперь бан, поэтому эта часть можно пропустить)
    # Оставим на всякий случай, если потом вернём мут

    # Анти-флуд (любые сообщения считаем)
    messages = user_messages[user_id]
    messages.append(now)
    # Удаляем старые, чтобы список не рос
    while messages and now - messages[0] > per_seconds:
        messages.pop(0)

    if len(messages) >= max_messages:
        # Удаляем сообщение с флудом
        try:
            await message.delete()
        except:
            pass

        # Увеличиваем счетчик предупреждений
        warnings[user_id]["count"] += 1
        warn_count = warnings[user_id]["count"]

        if warn_count >= 3:
            # Баним пользователя
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{update.effective_user.first_name} заблокирован за спам. 🚫",
                )

                # Логируем бан в канал
                await context.bot.send_message(
                    chat_id=log_channel_id,
                    text=(
                        f"👮‍♂️ Пользователь забанен за флуд:\n"
                        f"👤 ID: `{user_id}`\n"
                        f"📛 Имя: {update.effective_user.full_name}\n"
                        f"💬 Чат: {chat_id}\n"
                        f"🚫 Причина: 3+ предупреждений за {per_seconds} секунд"
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Ошибка при бане: {e}")
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{update.effective_user.first_name}, не флуди! Предупреждение {warn_count}/3 ⚠️",
                reply_to_message_id=message.message_id,
            )
        return

    # Обработка капчи для новых пользователей
    if user_id in pending_captcha:
        if text == CAPTCHA_ANSWER:
            # Снимаем ограничения
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await message.reply_text(t["captcha_passed"])
            del pending_captcha[user_id]
        else:
            await message.reply_text(t["captcha_failed"])


# --- Запуск бота ---

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", set_lang))

    app.add_handler(CallbackQueryHandler(on_lang_button, pattern="^(set_lang_|join_lang_)"))

    # Обработка новых участников через ChatMemberHandler
    from telegram.ext import ChatMemberHandler

    app.add_handler(ChatMemberHandler(on_user_join, ChatMemberHandler.CHAT_MEMBER))

    # Обработка любых сообщений (текст, фото, стикеры и др)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
