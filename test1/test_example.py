import pytest
import allure
from playwright.async_api import Page, expect


@allure.title("Поиск в Google с использованием надежных проверок")
@allure.feature("UI Тесты")
@pytest.mark.asyncio
async def test_google_search_robust(page: Page):
    error_occurred = False
    try:
        with allure.step("Открыть главную страницу Google"):
            await page.goto("https://www.google.com", wait_until="commit", timeout=10_000)

        with allure.step("Проверить заголовок страницы"):
            await expect(page).to_have_title("Google")

        with allure.step("Проверить видимость строки поиска"):
            search_input = page.get_by_role("combobox")
            await expect(search_input).to_be_visible(timeout=5_000)

    except Exception:
        # Скриншот только при ошибке теста
        screenshot = await page.screenshot(full_page=False)
        allure.attach(body=screenshot,
            name="Failure_Screenshot",
            attachment_type=allure.attachment_type.PNG,
            extension="png"
        )
        error_occurred = True
        raise
    finally:
        if not error_occurred:
            # Скриншот при успешном завершении теста
            screenshot = await page.screenshot(full_page=False)
            allure.attach(
                body=screenshot,
                name="Success_Screenshot",
                attachment_type=allure.attachment_type.PNG,
                extension="png"
            )