import pytest
import os
import nest_asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

# 1. Применяем патч для Windows сразу
nest_asyncio.apply()

@pytest.fixture(scope="session")
def extension_browser():
    with sync_playwright() as p:
        # 1) Динамический путь: берем корень проекта, где бы он ни лежал
        # os.getcwd() вернет путь к папке, из которой запущен pytest
        root_dir = os.getcwd()
        
        # Укажите путь к папке расширения внутри вашего репозитория
        ext_path = os.path.join(root_dir, "my_extension")

        # 2) Директория под временные данные (тоже в корне проекта)
        user_data_dir = os.path.join(root_dir, "user_data_temp")

        # 3) Запуск
        # headless=False ОБЯЗАТЕЛЕН для расширений, 
        # поэтому в GitHub Actions мы будем использовать xvfb-run
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, 
            args=[
                f"--disable-extensions-except={ext_path}",
                f"--load-extension={ext_path}",
                "--no-sandbox", # Важно для работы в Docker/Linux контейнерах
                "--disable-setuid-sandbox"
            ],
        )

        yield context
        context.close()

@pytest.fixture(scope="function")
async def page():
    # 2. Запускаем движок Playwright
    async with async_playwright() as p:
        # 3. Сначала запускаем сам браузер
        browser = await p.chromium.launch(headless=True)

        # 4. Теперь создаем контекст с нужным User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # 5. Создаем страницу в этом контексте
        page = await context.new_page()

        # 6. Отдаем страницу в тест
        yield page

        # 7. После теста всё закрываем
        await browser.close()