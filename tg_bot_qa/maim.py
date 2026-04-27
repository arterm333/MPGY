import asyncio
import os
import requests

from aiogram import Bot, Dispatcher, types  # pyright: ignore[reportMissingImports]
from aiogram.filters import Command  # pyright: ignore[reportMissingImports]
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup  # pyright: ignore[reportMissingImports]

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
WORKFLOW_ID = os.getenv("WORKFLOW_ID", "tests.yml")
WORKFLOW_REF = os.getenv("WORKFLOW_REF", "main")

required_vars = {
    "TELEGRAM_BOT_TOKEN": API_TOKEN,
    "GITHUB_TOKEN": GITHUB_TOKEN,
    "REPO_OWNER": REPO_OWNER,
    "REPO_NAME": REPO_NAME,
}
missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем удобные кнопки в интерфейсе
kb = [
    [KeyboardButton(text="/run_smoke_tests")],
    [KeyboardButton(text="/run_dszn_136200_test")],
    [KeyboardButton(text="/check_status")]
]
keyboard = ReplyKeyboardMarkup(
    keyboard=kb, 
    resize_keyboard=True,
    input_field_placeholder="Выберите тест для запуска"
)

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
    data = {"ref": WORKFLOW_REF} # Ветка, из которой запускаем тесты

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        await message.answer("✅ Пайплайн запущен! Результаты придут через пару минут.")
    else:
        await message.answer(f"❌ Ошибка запуска: {response.status_code}\n{response.text}")

@dp.message(Command("run_dszn"))
async def run_dszn_test(message: types.Message):
    await message.answer("🚀 Запускаю специфический тест: dszn136200.py")

    url = f"https://api.api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Ключевой момент: добавляем словарь inputs
    data = {
        "ref": "main", 
        "inputs": {
            "test_file": "Forms/dszn136200.py" # Точный путь к файлу в репозитории
        }
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 204:
        await message.answer("✅ GitHub принял задачу на конкретный тест.")
    else:
        await message.answer(f"❌ Ошибка: {response.status_code}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())