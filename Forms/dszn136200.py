import os

from test1.user.user import user_fl
import pytest
import allure
from playwright.sync_api import expect, sync_playwright



def test_dszn136200_new_application_button(extension_browser):
    url = "https://dszn136200.fogu.srvdev.ru/pgu2/136200"

    # В persistent context первая вкладка уже открыта
    page = extension_browser.pages[0] if extension_browser.pages else extension_browser.new_page()

    with allure.step("Открыть страницу DSZN136200"):
        page.route("**/*", user_fl)
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)

    with allure.step('Проверить наличие кнопки "Продолжить"'):
        # Используем роль button и точное имя. Если у сайта окажется, что это link/другая роль,
        # скажи — адаптирую селектор.
        new_app_button = page.get_by_role("button", name="Продолжить")
        expect(new_app_button).to_be_visible(timeout=15_000)

    with allure.step('Проверить доступность кнопки "Продолжить"'):
        # Доступность считаем как "включена" (не disabled)
        expect(new_app_button).to_be_enabled()

