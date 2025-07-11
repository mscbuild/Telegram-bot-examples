from telebot.async_telebot import AsyncTeleBot
import asyncio

bot = AsyncTeleBot("Your_token_bot")

@bot.message_handler(func=lambda message: True)
async def echo(message):
    await bot.send_message(message.chat.id, f"Ты написал: {message.text}")

if __name__ == "__main__":
    print("✅ Бот запущен")
    asyncio.run(bot.polling())
