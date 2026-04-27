import asyncio
import requests

from aiogram import Bot, Dispatcher, types  # pyright: ignore[reportMissingImports]
from aiogram.filters import Command  # pyright: ignore[reportMissingImports]
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup  # pyright: ignore[reportMissingImports]

# Вставьте сюда токен, который дал BotFather
API_TOKEN = '8360653159:AAEtsQkTW6FOS-F7T2pBPlOXVpUmHXaVk8A'
GITHUB_TOKEN = 'ВАШ_GITHUB_TOKEN'
REPO_OWNER = 'ВАШ_LOGИН_GITHUB'
REPO_NAME = 'НАЗВАНИЕ_РЕПОЗИТОРИЯ'
WORKFLOW_ID = 'tests.yml'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем удобные кнопки в интерфейсе
kb = [
    [KeyboardButton(text="/run_smoke_tests")],
    [KeyboardButton(text="/check_status")]
]
keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для управления автотестами. Выбери действие:",
        reply_markup=keyboard
    )

@dp.message(Command("run_smoke_tests"))
async def run_tests(message: types.Message):
    await message.answer("🚀 Посылаю сигнал на GitHub Actions...")

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"} # Ветка, из которой запускаем тесты

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        await message.answer("✅ Пайплайн запущен! Результаты придут через пару минут.")
    else:
        await message.answer(f"❌ Ошибка запуска: {response.status_code}\n{response.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())