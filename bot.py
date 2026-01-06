import os
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
SERVICE_ACCOUNT_FILE = os.environ.get("SERVICE_ACCOUNT_FILE")

if not TELEGRAM_TOKEN or not SPREADSHEET_ID or not SERVICE_ACCOUNT_FILE:
    logger.error("Не установлены необходимые переменные окружения!")
    raise RuntimeError("TELEGRAM_TOKEN, SPREADSHEET_ID и SERVICE_ACCOUNT_FILE должны быть установлены.")

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Пример команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}! Бот запущен успешно.")

# Основной запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Запуск бота
    logger.info("Бот запущен...")
    app.run_polling()
