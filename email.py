import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiosmtplib import SMTP
from telebot.async_telebot import AsyncTeleBot

# ====== НАСТРОЙКИ ======
EMAIL = 'example@mail.com'          # Почта, с которой отправляется
EMAIL_PWD = 'your_password'          # Пароль от почты (в настройках почты)
EMAIL_TO = 'example@mail.com'       # Куда отправлять (тот же адрес, фиксированный)

SMTP_HOST = 'smtp.yandex.ru'
SMTP_PORT = 465

TELEGRAM_TOKEN = 'your_telegram_bot_token'  # Замените на реальный токен

# ====== ИНИЦИАЛИЗАЦИЯ БОТА ======
bot = AsyncTeleBot(TELEGRAM_TOKEN)

# ====== ФУНКЦИЯ ОТПРАВКИ ПИСЬМА ======
async def send_mail(subject, to, msg_html):
    message = MIMEMultipart()
    message["From"] = EMAIL
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(f"<html><body>{msg_html}</body></html>", "html", "utf-8"))

    smtp_client = SMTP(hostname=SMTP_HOST, port=SMTP_PORT, use_tls=True)
    await smtp_client.connect()
    await smtp_client.login(EMAIL, EMAIL_PWD)
    await smtp_client.send_message(message)
    await smtp_client.quit()

# ====== ОБРАБОТЧИК /start ======
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.send_message(message.chat.id, "Привет! Напиши 'письмо', чтобы отправить сообщение на email.")

# ====== ОБРАБОТЧИК СООБЩЕНИЯ 'письмо' ======
@bot.message_handler(func=lambda message: message.text.lower() == 'письмо')
async def handle_send_mail(message):
    await bot.send_message(message.chat.id, "📨 Отправляю письмо...")

    try:
        await send_mail(
            subject="Новое сообщение от Telegram-бота",
            to=EMAIL_TO,
            msg_html=f"<p>📩 Сообщение от пользователя Telegram</p><p>User ID: <strong>{message.from_user.id}</strong></p>"
        )
        await bot.send_message(message.chat.id, "✅ Письмо успешно отправлено на email!")
    except Exception as e:
        await bot.send_message(message.chat.id, f"❌ Ошибка при отправке: {e}")

# ====== ЗАПУСК ======
if __name__ == '__main__':
    print("🤖 Бот запущен. Ожидаю команду 'письмо'...")
    asyncio.run(bot.polling())
