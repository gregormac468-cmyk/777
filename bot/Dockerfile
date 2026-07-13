FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Код приложения
COPY src/ ./src/
COPY content/ ./content/

# Данные (volume)
RUN mkdir -p /app/data

CMD ["python", "-m", "src.main"]
