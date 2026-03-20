import os
import subprocess


def run_automation():
    # 1. Путь к результатам
    results_dir = "allure-results"

    print("--- Запуск тестов Playwright ---")
    # 2. Запуск pytest (флаг --headed чтобы видеть браузер)
    # Используем subprocess.run для ожидания завершения тестов
    pytest_cmd = f"pytest --headed --alluredir={results_dir} test1/test_example.py"
    subprocess.run(pytest_cmd, shell=True)

    print("\n--- Генерация и открытие отчета Allure ---")
    # 3. Запуск Allure сервера
    # Это откроет браузер с отчетом. Чтобы остановить, нажмите Ctrl+C в терминале.
    allure_cmd = f"allure serve {results_dir}"
    subprocess.run(allure_cmd, shell=True)


if __name__ == "__main__":
    run_automation()