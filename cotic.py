import discord
from discord.ext import commands

# Включаем нужные намерения
intents = discord.Intents.default()
intents.members = True  # Нужно для выдачи ролей
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# НАСТРОЙКА: Замените ID на свои (без кавычек)
TARGET_MESSAGE_ID = 123456789012345678  # ID сообщения, под которым нужно ставить реакции
ROLE_ID = 876543210987654321            # ID роли, которую бот будет выдавать
EMOJI = "✅"                            # Эмодзи (можно использовать стандартный)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")

@bot.event
async def on_raw_reaction_add(payload):
    """Срабатывает, когда кто-то ставит реакцию"""
    # Проверяем, то ли это сообщение
    if payload.message_id != TARGET_MESSAGE_ID:
        return
        
    # Проверяем, тот ли это эмодзи
    if str(payload.emoji) != EMOJI:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    # Получаем пользователя и роль
    member = guild.get_member(payload.user_id)
    role = guild.get_role(ROLE_ID)

    # Игнорируем самого бота и проверяем существование роли
    if member and role and not member.bot:
        await member.add_roles(role)
        print(f"Роль {role.name} выдана пользователю {member.name}")

@bot.event
async def on_raw_reaction_remove(payload):
    """Срабатывает, когда кто-то убирает реакцию (забирает роль)"""
    if payload.message_id != TARGET_MESSAGE_ID:
        return
        
    if str(payload.emoji) != EMOJI:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    member = guild.get_member(payload.user_id)
    role = guild.get_role(ROLE_ID)

    if member and role and not member.bot:
        await member.remove_roles(role)
        print(f"Роль {role.name} убрана у пользователя {member.name}")

# Замените ТОКЕН на ваш ключ из Developer Portal
bot.run("ВАШ_ТОКЕН_БОТА")
