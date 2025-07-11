import logging
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from datetime import datetime
import io
import os

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_FILE = "finance.csv"
CATEGORIES = ["🏠 Квартира", "🍽️ Еда", "🛍️ Покупки", "📎 Другое"]
currency = "€"

# --- Состояния диалога ---
INCOME_AMOUNT, EXPENSE_CATEGORY, EXPENSE_AMOUNT = range(3)

# --- Главное меню ---
def get_main_menu():
    keyboard = [
        ["💶 Приход", "💸 Расход"],
        ["📊 Баланс", "📈 Диаграмма"],
        ["📁 Экспорт", "🗑️ Стереть данные"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === Команда /help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Доступные команды:\n"
        "/start — Запуск бота\n"
        "/help — Помощь\n"
        "/balance — Показать баланс\n"
        "/report — Показать отчёт\n"
        "/chart — Показать диаграмму расходов\n"
        "/export — Экспортировать данные в CSV\n"
        "/delete_data — Удалить все данные\n"
        "Вы можете также выбрать действия с помощью кнопок ниже:",
        reply_markup=get_main_menu()
    )

# --- Стартовая команда ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для учёта финансов. Выберите действие:",
        reply_markup=get_main_menu()
    )

# --- Обработка кнопок ---
async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💶 Приход":
        return await add_income(update, context)
    elif text == "💸 Расход":
        return await add_expense(update, context)
    elif text == "📊 Баланс":
        return await balance(update, context)
    elif text == "📈 Диаграмма":
        return await chart(update, context)
    elif text == "📁 Экспорт":
        return await export_csv(update, context)
    elif text == "🗑️ Стереть данные":
        return await delete_data(update, context)

# --- Удаление всех данных ---
async def delete_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        await update.message.reply_text("✅ Все данные удалены.", reply_markup=get_main_menu())
    else:
        await update.message.reply_text("❌ Нет данных для удаления.", reply_markup=get_main_menu())

# --- Добавление дохода ---
async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    await update.message.reply_text("💶 Введите сумму дохода:", reply_markup=reply_markup)
    return INCOME_AMOUNT

async def save_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        return await start(update, context)
    try:
        amount = float(text)
        save_to_csv("Приход", amount, None)
        await update.message.reply_text(f"✅ Доход {amount:.2f}{currency} добавлен.", reply_markup=get_main_menu())
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число.")
        return INCOME_AMOUNT
    return ConversationHandler.END

# --- Добавление расхода ---
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([[cat] for cat in CATEGORIES] + [["🔙 Назад"]], resize_keyboard=True)
    await update.message.reply_text("📂 Выберите категорию расхода:", reply_markup=reply_markup)
    return EXPENSE_CATEGORY

async def get_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    if category == "🔙 Назад":
        return await start(update, context)
    if category not in CATEGORIES:
        await update.message.reply_text("❌ Пожалуйста, выберите категорию из списка.")
        return EXPENSE_CATEGORY
    context.user_data["category"] = category
    reply_markup = ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    await update.message.reply_text(f"💸 Введите сумму расхода для '{category}':", reply_markup=reply_markup)
    return EXPENSE_AMOUNT

async def save_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        return await start(update, context)
    try:
        amount = float(text)
        category = context.user_data["category"]
        save_to_csv("Расход", amount, category)
        await update.message.reply_text(f"✅ Расход {amount:.2f}{currency} в категории '{category}' добавлен.", reply_markup=get_main_menu())
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число.")
        return EXPENSE_AMOUNT
    return ConversationHandler.END

# --- Сохранение в CSV ---
def save_to_csv(type_, amount, category):
    df = pd.DataFrame([{
        "Дата": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Тип": type_,
        "Сумма": amount,
        "Категория": category or ""
    }])
    df.to_csv(CSV_FILE, mode='a', index=False, header=not pd.io.common.file_exists(CSV_FILE))

# --- Баланс ---
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pd.io.common.file_exists(CSV_FILE):
        await update.message.reply_text("❌ Нет данных.", reply_markup=get_main_menu())
        return

    df = pd.read_csv(CSV_FILE)
    income = df[df["Тип"] == "Приход"]["Сумма"].sum()
    expense = df[df["Тип"] == "Расход"]["Сумма"].sum()
    bal = income - expense
    await update.message.reply_text(
        f"📊 Баланс: {bal:.2f}{currency}\n"
        f"Доход: {income:.2f}{currency}, Расход: {expense:.2f}{currency}",
        reply_markup=get_main_menu()
    )

# --- Диаграмма расходов ---
async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pd.io.common.file_exists(CSV_FILE):
        await update.message.reply_text("❌ Нет данных для построения диаграммы.", reply_markup=get_main_menu())
        return

    df = pd.read_csv(CSV_FILE)
    expense_df = df[df["Тип"] == "Расход"]

    if expense_df.empty:
        await update.message.reply_text("❌ Нет данных о расходах.", reply_markup=get_main_menu())
        return

    summary = expense_df.groupby("Категория")["Сумма"].sum()
    
    if summary.empty:
        await update.message.reply_text("❌ Нет данных по категориям расходов.", reply_markup=get_main_menu())
        return

    # Построение диаграммы
    fig, ax = plt.subplots()
    summary.plot(kind="pie", autopct="%1.1f%%", ylabel="", ax=ax)
    plt.title("💸 Расходы по категориям")
    plt.tight_layout()

    # Используем BytesIO для сохранения изображения в памяти
    buf_pie = io.BytesIO()
    try:
        # Сохраняем диаграмму в буфер памяти
        plt.savefig(buf_pie, format="png")
        buf_pie.seek(0)  # Перемещаем указатель в начало буфера
        plt.close()  # Закрываем график

        # Отправляем диаграмму пользователю
        await update.message.reply_photo(photo=buf_pie, reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при отправке диаграммы: {e}")
        await update.message.reply_text("❌ Ошибка при отправке диаграммы.", reply_markup=get_main_menu())

# --- Экспорт в CSV ---
async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if pd.io.common.file_exists(CSV_FILE):
            with open(CSV_FILE, "rb") as f:
                await update.message.reply_document(document=f, reply_markup=get_main_menu())
        else:
            await update.message.reply_text("❌ Нет данных для экспорта.", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при экспорте CSV: {e}")
        await update.message.reply_text("❌ Ошибка при экспорте данных.", reply_markup=get_main_menu())

# --- Отмена / Назад ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Операция отменена.", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- Основной запуск ---
def main():
    # Создание приложения с токеном
    app = ApplicationBuilder().token("Your_token").build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("export", export_csv))
    app.add_handler(CommandHandler("help", help_command))

    # Обработчики для добавления дохода и расхода
    income_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("💶 Приход"), add_income)],
        states={
            INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_income)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    expense_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("💸 Расход"), add_expense)],
        states={
            EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_expense_category)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_expense)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Добавляем обработчики для конверсий
    app.add_handler(income_conv)
    app.add_handler(expense_conv)

    # Обработчик нажатий на кнопки
    app.add_handler(MessageHandler(filters.TEXT, handle_button_press))

    # Запуск бота
    print("✅ Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()

