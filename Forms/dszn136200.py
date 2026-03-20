import os

from test1.user.user import user_fl
import pytest
import allure
from playwright.sync_api import expect, sync_playwright


@pytest.fixture(scope="session")
def extension_browser():
  

    with sync_playwright() as p:
        # 1) Путь к папке с РАСПАКОВАННЫМ расширением (там где лежит manifest.json)
        ext_path = os.path.abspath(
            r"C:\Users\user\AppData\Local\Google\Chrome\User Data\Profile 4\Extensions\idgpnmonknjnojddfkpgkljpfnnfcklj\7.0.14_1"
        )

        # 2) Отдельная директория под временные данные профиля (cookies/cache и т.д.)
        user_data_dir = os.path.abspath("./user_data_dszn136200_forms")

        # 3) Запуск через launch_persistent_context
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,  # ВАЖНО: расширения не работают в headless режиме
            args=[
                f"--disable-extensions-except={ext_path}",
                f"--load-extension={ext_path}",
            ],
        )

        yield context
        context.close()


def test_dszn136200_new_application_button(extension_browser):
    url = "https://dszn136200.fogu.srvdev.ru/pgu2/136200"

    # В persistent context первая вкладка уже открыта
    page = extension_browser.pages[0] if extension_browser.pages else extension_browser.new_page()

    with allure.step("Открыть страницу DSZN136200"):
        page.route("**/*", user_fl)
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)

    with allure.step('Проверить наличие кнопки "Новое заявление"'):
        # Используем роль button и точное имя. Если у сайта окажется, что это link/другая роль,
        # скажи — адаптирую селектор.
        new_app_button = page.get_by_role("button", name="Новое заявление")
        expect(new_app_button).to_be_visible(timeout=15_000)

    with allure.step('Проверить доступность кнопки "Новое заявление"'):
        # Доступность считаем как "включена" (не disabled)
        expect(new_app_button).to_be_enabled()

