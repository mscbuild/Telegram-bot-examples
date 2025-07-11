import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# 🔐 Вставь свои ключи здесь
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Инициализация OpenAI
openai.api_key = OPENAI_API_KEY

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот с искусственным интеллектом ChatGPT.\n"
        "Просто задай мне вопрос, и я постараюсь ответить. 🧠"
    )

# Обработка текстов — ChatGPT
async def handle_chatgpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Уведомление, что бот обрабатывает
    await update.message.reply_text("🤔 Думаю...")

    try:
        # Запрос к OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # или "gpt-4"
            messages=[
                {"role": "system", "content": "Ты дружелюбный и умный Telegram-бот помощник."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000,
            n=1,
        )

        reply = response.choices[0].message["content"].strip()

        await update.message.reply_text(reply)

    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке запроса. Попробуй снова позже.")

# Запуск бота
async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chatgpt))

    print("✅ Бот запущен...")
    await application.run_polling()

# Точка входа
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

