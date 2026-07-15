FROM python:3.12-slim

# Устанавливаем системные зависимости, tzdata и Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    ca-certificates \
    fonts-liberation \
    tzdata \
    gnupg \
    --no-install-recommends \
    # Настраиваем часовой пояс Europe/Moscow
    && ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && echo "Europe/Moscow" > /etc/timezone \
    # Добавляем официальный репозиторий Google Chrome (по новому стандарту)
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    # Очищаем кэш apt, чтобы образ не весил лишнего
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем системную переменную времени для Python
ENV TZ=Europe/Moscow

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]
