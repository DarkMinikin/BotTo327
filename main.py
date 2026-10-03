import os
import discord
from discord.ext import tasks, commands
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

import config

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

SCOPES = [
    "https://googleapis.com",
    "https://googleapis.com"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Словарь для отслеживания изменений, чтобы избежать спама
last_sent_values = {}

def process_sheet_data():
    """Сканирует первый лист и находит нужные специализации в строках руководства"""
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Получаем данные со всего первого листа в виде списка списков (матрицы ячеек)
        # Мы используем get_all_values(), чтобы видеть реальные индексы столбцов (А=1, B=2, C=3...)
        sheet = client.open(config.GOOGLE_SHEET_NAME).sheet1
        all_rows = sheet.get_all_values()
        
        found_data = {}
        # Счетчик для одноименных должностей (например, чтобы различить двух "Зам. КМД")
        leader_counts = {}

        for row in all_rows:
            # Ищем, есть ли в текущей строке какая-либо из должностей руководства
            detected_leader = None
            for leader in config.LEADER_ROLES:
                if leader in row:
                    detected_leader = leader
                    break
            
            # Если в этой строке сидит КМД / Зам. КМД / КМД спец.
            if detected_leader:
                # Ведем учет дубликатов должностей для красивого вывода
                leader_counts[detected_leader] = leader_counts.get(detected_leader, 0) + 1
                instance_id = f" [{leader_counts[detected_leader]}]" if leader_counts[detected_leader] > 1 else ""

                # Проверяем, есть ли в этой же строке нужная специализация (AAT, HG, CD...)
                for spec in config.TARGET_SPECS:
                    if spec in row:
                        # Столбец C — это 3-й элемент строки (индекс 2 в Python, так как отсчет с 0)
                        # Защита от коротких или пустых строк в таблице
                        if len(row) >= 3:
                            c_value = row[2].strip() # Забираем значение столбца C
                            
                            # Формируем уникальный ключ, например: "Зам. КМД [2] (HG)" или "КМД (AAT)"
                            unique_key = f"{detected_leader}{instance_id} ({spec})"
                            found_data[unique_key] = c_value

        return found_data
    except Exception as e:
        print(f"Ошибка при обработке таблицы: {e}")
        return None

@bot.event
async def on_ready():
    print(f"Бот {bot.user.name} успешно запущен!")
    check_google_sheets.start()

@tasks.loop(minutes=config.CHECK_INTERVAL_MINUTES)
async def check_google_sheets():
    global last_sent_values
    await bot.wait_until_ready()
    
    channel = bot.get_channel(config.CHANNEL_ID)
    if not channel:
        print(f"Ошибка: Не найден канал {config.CHANNEL_ID}")
        return

    # Получаем отфильтрованные данные
    current_mapped_data = process_sheet_data()
    if current_mapped_data is None:
        return

    # Проверяем изменения по каждой найденной связке должность+спецификация
    for unique_name, current_value in current_mapped_data.items():
        old_value = last_sent_values.get(unique_name)
        
        # Если значение в столбце С изменилось или появилось впервые
        if current_value != old_value:
            # Избегаем спама при самом первом включении бота
            if old_value is not None:
                message = f"📋 **Обновление структуры для {unique_name}**:\nДанные из столбца C: `{current_value}`"
                await channel.send(message)
            
            # Обновляем сохраненное значение
            last_sent_values[unique_name] = current_value

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
