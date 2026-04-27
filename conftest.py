import pytest
import nest_asyncio
from playwright.async_api import async_playwright

# 1. Применяем патч для Windows сразу
nest_asyncio.apply()


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