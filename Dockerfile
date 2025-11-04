# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем директорию для постоянного хранилища
RUN mkdir -p /data && chmod 777 /data

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код (исключая .env для безопасности)
COPY *.py .
COPY requirements.txt .
COPY *.md .

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && chown -R app:app /data

# Переключаемся на пользователя app
USER app

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открываем порт (если потребуется для веб-интерфейса)
EXPOSE 8000

# Команда запуска
CMD ["python", "run.py"]