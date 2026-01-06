import os
import hashlib
import re
import tempfile
import pdfplumber
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# Настройки (редактируешь здесь)
# -------------------------
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')  # Render: задаём переменные окружения
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')  # ID Google Sheet
SERVICE_ACCOUNT_FILE = 'service_account.json'      # JSON ключ загружается в проект

# -------------------------
# Инициализация Google Sheets
# -------------------------
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=scopes
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# -------------------------
# Функция для проверки дублей
# -------------------------
def is_duplicate(row_hash):
    existing_hashes = sheet.col_values(7)  # 7-я колонка: Hash
    return row_hash in existing_hashes

# -------------------------
# Функция парсинга PDF
# -------------------------
def parse_pdf(file_path):
    rows = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                # Пропускаем пустые или итоговые строки
                if not line.strip() or 'Всего' in line:
                    continue

                # Пример строки:
                # 1 Услуги по стирке и полной обработке белья (17.12.2025) 28.2 кг 70.00 1 974.00
                # Регулярка для даты
                date_match = re.search(r'\((\d{2}\.\d{2}\.\d{4})\)', line)
                date = date_match.group(1) if date_match else ''

                # Убираем дату из наименования
                line_clean = re.sub(r'\(\d{2}\.\d{2}\.\d{4}\)', '', line)

                # Разбиваем на части
                parts = line_clean.split()
                if len(parts) < 3:
                    continue  # слишком короткая строка

                no = parts[0]
                # Наименование — всё до кол-во (приблизительно)
                naim_match = re.search(r'^\d+\s+(.+?)\s+([\d,.]+\s*\S+)', line_clean)
                if naim_match:
                    naim = naim_match.group(1).strip()
                    qty_unit = naim_match.group(2).strip()
                    qty_parts = qty_unit.split()
                    qty = qty_parts[0].replace(',', '.')
                    unit = qty_parts[1] if len(qty_parts) > 1 else ''
                else:
                    naim = ' '.join(parts[1:-3])
                    qty = parts[-3].replace(',', '.')
                    unit = parts[-2]

                # Цена и сумма (берем последние 2 числа)
                try:
                    price = parts[-2].replace(',', '.').replace(' ', '')
                    summa = parts[-1].replace(',', '.').replace(' ', '')
                except IndexError:
                    price = '0'
                    summa = '0'

                # Хеш для проверки дублей
                row_hash = hashlib.md5(f"{date}{naim}{summa}".encode('utf-8')).hexdigest()

                # Проверка дубля
                if is_duplicate(row_hash):
                    continue

                # Добавляем строку
                row = [no, date, naim, qty, unit, price, summa, row_hash]
                rows.append(row)

    return rows

# -------------------------
# Обработка входящих сообщений
# -------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file = update.message.document
        if file.mime_type in ['application/pdf']:
            with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
                path = tmp.name
                await file.get_file().download_to_drive(path)
                new_rows = parse_pdf(path)
                for row in new_rows:
                    # Запись в Google Sheets (без хеша)
                    sheet.append_row(row[:-1])
                if new_rows:
                    await update.message.reply_text(f"Добавлено {len(new_rows)} строк в таблицу.")
                else:
                    await update.message.reply_text("Дубли не добавлены.")
        else:
            await update.message.reply_text("Только PDF поддерживаются.")

# -------------------------
# Главная функция
# -------------------------
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    print("Бот запущен...")
    app.run_polling()
