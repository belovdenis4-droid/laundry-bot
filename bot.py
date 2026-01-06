import logging
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pdfplumber
import os

# -------------------------
# Настройка логирования
# -------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------
# Конфигурация
# -------------------------
# Правильный путь к JSON с ключами Google Service Account
SERVICE_ACCOUNT_FILE = '/etc/secrets/tg2sheet-abb9235438d2.json'
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Telegram токен через environment variable
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# -------------------------
# Авторизация Google Sheets
# -------------------------
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    # Пример: открытие листа по названию
    sheet = client.open("YourSpreadsheetName").sheet1
except FileNotFoundError:
    logger.error(f"Файл сервисного аккаунта не найден: {SERVICE_ACCOUNT_FILE}")
    raise
except Exception as e:
    logger.error(f"Ошибка при авторизации Google Sheets: {e}")
    raise

# -------------------------
# Функции бота
# -------------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я готов обрабатывать PDF и записывать данные в Google Sheets.")

def handle_pdf(update: Update, context: CallbackContext):
    if not update.message.document:
        update.message.reply_text("Пожалуйста, пришлите PDF файл.")
        return
    
    file = update.message.document.get_file()
    file_path = f"/tmp/{update.message.document.file_name}"
    file.download(file_path)
    
    # Парсим PDF
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        update.message.reply_text(f"Ошибка при обработке PDF: {e}")
        return

    # Добавляем текст в Google Sheet
    try:
        sheet.append_row([update.message.from_user.username, text])
        update.message.reply_text("Данные успешно добавлены в Google Sheet!")
    except Exception as e:
        update.message.reply_text(f"Ошибка при записи в Google Sheet: {e}")

# -------------------------
# Основной запуск бота
# -------------------------
def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не установлен в environment variables")
        return
    
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
