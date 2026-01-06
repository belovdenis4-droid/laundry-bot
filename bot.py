import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ===== Настройки =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

# Путь к секретному файлу сервис-аккаунта
SERVICE_ACCOUNT_FILE = "/etc/secrets/tg2sheet-abb9235438d2.json"  # <- точно такое имя, какое у вас в Render

# ===== Подключение к Google Sheets =====
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # Используем первый лист

# ===== Функции бота =====
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я готов принимать данные для Google Sheets.")

def echo(update: Update, context: CallbackContext):
    text = update.message.text
    # Добавляем новую строку в конец таблицы
    sheet.append_row([text])
    update.message.reply_text(f"Данные добавлены: {text}")

# ===== Основная функция =====
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
