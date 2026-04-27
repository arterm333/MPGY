# Используем официальный образ Playwright, в котором уже есть все браузеры и зависимости Linux
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Устанавливаем переменную окружения для работы дисплея (нужно для расширений)
ENV DISPLAY=:99

# Команда для запуска: поднимаем виртуальный дисплей и запускаем pytest
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x1024x24 & pytest"]