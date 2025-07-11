from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Отчёт", callback_data='report')],
        [InlineKeyboardButton("❓ Вопрос", callback_data='question')],
        [InlineKeyboardButton("📋 Список задач", callback_data='tasks')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник. Выбери действие:", 
        reply_markup=get_main_menu()
    )

# Обработка кнопок меню
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'report':
        await query.edit_message_text("📈 Еженедельный отчёт:\n\n🗓 Неделя: 24 июня – 30 июня\n✅ Задач выполнено: 12\n❗ Просрочено: 2\n📌 Новых задач: 5")

    elif query.data == 'question':
        await query.edit_message_text("❓ Напиши мне свой вопрос, и я постараюсь помочь!")

    elif query.data == 'tasks':
        tasks = [
            "✅ Завершить презентацию",
            "🕐 Запланировать встречу",
            "❗ Написать отчёт по проекту",
            "📞 Позвонить клиенту"
        ]
        task_list = "\n".join(tasks)
        await query.edit_message_text(f"📋 Текущие задачи:\n\n{task_list}")

# Ответ на текстовые сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()

    if "привет" in msg:
        await update.message.reply_text("👋 Привет! Чем могу помочь?")
    elif "отчёт" in msg:
        await update.message.reply_text("📊 Твой последний отчёт доступен по кнопке 'Отчёт' в меню.")
    else:
        await update.message.reply_text("🤔 Я пока не понимаю это сообщение. Используй меню!")

# Запуск приложения
app = ApplicationBuilder().token("Your_token_bot").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Бот запущен...")
app.run_polling()
