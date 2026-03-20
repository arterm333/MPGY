import pytest
import allure
from playwright.async_api import Page, expect


@allure.title("Проверка видимости кнопки 'История' на YouTube")
@allure.feature("UI Тесты")
@pytest.mark.asyncio
async def test_youtube_history_button_visible(page: Page) -> None:
    """
    Тест проверяет, что на YouTube в русской локали:
    - левое меню успешно открывается по клику на кнопку «Гид»;
    - ссылка «История» присутствует в меню и видна без дополнительного скролла;
    - используется надёжный селектор a[title="История"][href="/feed/history"].
    """

    # Флаг, чтобы понимать, делать скриншот как "успешный" или "на падении"
    error_occurred = False

    try:
        with allure.step("Открыть главную страницу YouTube в русской локали"):
            # Открываем главную страницу YouTube c параметрами локали, ждём domcontentloaded для устойчивости
            await page.goto(
                "https://www.youtube.com/?hl=ru&gl=RU",
                wait_until="domcontentloaded",
                timeout=60_000,
            )

        with allure.step("Убедиться, что шапка сайта (masthead) отрисована"):
            # Локатор шапки YouTube; её видимость косвенно подтверждает успешную загрузку страницы
            masthead = page.locator("ytd-masthead")
            await expect(masthead).to_be_visible(timeout=10_000)

        with allure.step("Открыть левое меню через кнопку 'Гид'"):
            # Находим кнопку открытия левого меню по aria-label, чтобы селектор был устойчивым к верстке
            guide_button = page.locator("button[aria-label='Гид']")
            await expect(guide_button).to_be_visible(timeout=10_000)
            await guide_button.click()

        with allure.step("Найти и проверить видимость ссылки 'История'"):
            # Используем надёжный селектор: точное совпадение title и href для пункта меню "История"
            history_link = page.locator("a[title='История'][href='/feed/history']")
            await expect(history_link).to_be_visible(timeout=10_000)

        with allure.step("Проверить, что 'История' находится в пределах видимой области (без скролла)"):
            # bounding_box даёт координаты элемента относительно viewport; используем их для проверки скролла
            box = await history_link.bounding_box()
            assert box is not None, "Не удалось получить координаты элемента 'История'"
            viewport_height = page.viewport_size["height"] if page.viewport_size else 720
            assert 0 <= box["y"] <= viewport_height, "Кнопка 'История' должна быть видна без скролла"

    except Exception:
        # Скриншот страницы только при ошибке для анализа причины падения в Allure
        screenshot = await page.screenshot(full_page=False)
        allure.attach(
            body=screenshot,
            name="YouTube_History_Failure",
            attachment_type=allure.attachment_type.PNG,
            extension="png",
        )
        error_occurred = True
        raise

    finally:
        if not error_occurred:
            # Скриншот при успешном прохождении теста для фиксации корректного состояния UI
            screenshot = await page.screenshot(full_page=False)
            allure.attach(
                body=screenshot,
                name="YouTube_History_Success",
                attachment_type=allure.attachment_type.PNG,
                extension="png",
            )

