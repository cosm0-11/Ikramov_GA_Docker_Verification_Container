FROM python:3.11-slim

# Системные зависимости для mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements .
RUN pip install --no-cache-dir -r requirements

# Копируем весь проект
COPY . .

# Создаём нужные папки (keys, data/*)
RUN python -c "from core.paths import prepare_directories; prepare_directories()"

# Порт приложения
EXPOSE 8000

# Запуск через gunicorn
CMD ["gunicorn", "django_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
