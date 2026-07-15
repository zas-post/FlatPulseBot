FROM python:3.12-slim

# Устанавливаем системные зависимости и пакет часовых поясов tzdata
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    ca-certificates \
    fonts-liberation \
    tzdata \
    --no-install-recommends \
    && ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && echo "Europe/Moscow" > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем системную переменную времени для Python
ENV TZ=Europe/Moscow

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]
