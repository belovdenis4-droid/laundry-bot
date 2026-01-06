import os
import re
import pdfplumber
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Параметры Render ---
SERVICE_ACCOUNT_FILE = '/run/secrets/tg2sheet-abb9235438d2.json'
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# --- Подключение к Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # первый лист таблицы

# --- Функция для извлечения данных из PDF ---
def parse_pdf(file_path):
    rows = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                # Пример строки: "Услуги по стирке (17.12.2025) 28.2 кг 70.00 1 974.00"
                match = re.match(r'(.+?)\s*\((\d{2}\.\d{2}\.\d{4})\)\s+([\d.,]+)\s*(кг|шт|WT|)', line)
                if match:
                    description = match.group(1).strip()
                    date = match.group(2).strip()
                    quantity = match.group(3).replace(',', '.')
                    rows.append([date, description, quantity])
    return rows

# --- Функция для добавления данных в Google Sheets ---
def add_to_sheet(rows):
    for row in rows:
        sheet.append_row(row)

# --- Обработка документов от Telegram ---
def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    if not file.file_name.lower().endswith('.pdf'):
        update.message.reply_text("Пожалуйста, присылайте PDF-файлы.")
        return

    file_path = file.get_file().download(custom_path=f"/tmp/{file.file_name}")
    update.message.reply_text(f"Файл {file.file_name} загружен, обрабатываю...")

    rows = parse_pdf(file_path)
    if rows:
        add_to_sheet(rows)
        update.message.reply_text(f"Добавлено {len(rows)} строк в Google Sheets.")
    else:
        update.message.reply_text("Не удалось найти данные в PDF.")

# --- Старт команды ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Пришли PDF со счетами, и я занесу их в Google Sheets.")

# --- Запуск бота ---
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
