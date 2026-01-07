import os
import json
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import gspread
from google.oauth2.service_account import Credentials


# ---------- LOGGING ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# Исправлено: __name__ (с подчеркиваниями)
logger = logging.getLogger(__name__)


# ---------- ENV ----------
# Исправлено: используем ваши названия из Replit Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_JSON")
# Убедитесь, что SPREADSHEET_NAME тоже добавлен в Secrets!
SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не задан в Secrets")

if not GOOGLE_CREDENTIALS_JSON:
    raise RuntimeError("GOOGLE_JSON не задан в Secrets")

if not SPREADSHEET_NAME:
    raise RuntimeError("SPREADSHEET_NAME не задан в Secrets")


# ---------- GOOGLE SHEETS ----------
try:
    credentials_dict = json.loads(GOOGLE_CREDENTIALS_JSON)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        credentials_dict,
        scopes=scopes
    )

    gclient = gspread.authorize(creds)

    # Проверка — если имя таблицы неверное, упадёт сразу
    sheet = gclient.open(SPREADSHEET_NAME).sheet1
except Exception as e:
    logger.error(f"Ошибка подключения к Google Sheets: {e}")
    raise


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и Google Sheets подключён ✅")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # gspread синхронная библиотека, в идеале её нужно запускать в потоке, 
        # но для теста 'ping' сработает и так.
        value = sheet.acell("A1").value
        await update.message.reply_text(f"A1 в таблице: {value}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении таблицы: {e}")


# ---------- MAIN ----------
async def main():
    # Инициализация приложения
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    logger.info("Бот запускается...")
    
    # В новых версиях python-telegram-bot для Replit/скриптов 
    # лучше использовать этот метод:
    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    
    # Держим бота запущенным
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
