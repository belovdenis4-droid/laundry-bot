import logging
import os
import pdfplumber

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# ЛОГИ
# -------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -------------------------
# ENV
# -------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

SERVICE_ACCOUNT_FILE = "/etc/secrets/tg2sheet-abb9235438d2.json"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# -------------------------
# GOOGLE SHEETS
# -------------------------
creds = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, SCOPE
)
gclient = gspread.authorize(creds)

# ❗️ ВАЖНО: замени на реальное имя таблицы
sheet = gclient.open("Счета прачки").sheet1

# -------------------------
# HANDLERS
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли PDF — я загружу данные в Google Sheets."
    )


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if document.mime_type != "application/pdf":
        await update.message.reply_text("Это не PDF файл.")
        return

    file = await document.get_file()
    file_path = f"/tmp/{document.file_name}"
    await file.download_to_drive(file_path)

    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        sheet.append_row([
            update.message.from_user.username or "unknown",
            text[:49000],  # защита от лимита ячеек
        ])

        await update.message.reply_text("PDF успешно обработан и записан ✅")

    except Exception as e:
        logger.exception("Ошибка обработки PDF")
        await update.message.reply_text(f"Ошибка: {e}")


# -------------------------
# MAIN
# -------------------------
def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
