import logging
import random
import undetected_chromedriver as uc


class BaseScraper:
    def __init__(self):
        pass

    def get_clean_options(self):
        """Генерирует новый независимый объект настроек Chrome"""
        options = uc.ChromeOptions()

        # Настройки для стабильности в Docker
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--blink-settings=imagesEnabled=false")

        # 🔥 Изолируем порты отладки, чтобы потоки Авито и Циана не конфликтовали за один порт
        random_port = random.randint(10000, 20000)
        options.add_argument(f"--remote-debugging-port={random_port}")

        # 🔥 Маскировка: отключаем кэш и добавляем реальный User-Agent
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-gpu")
        options.add_argument("--crash-dumps-dir=/tmp")

        # Дополнительная имитация обычного пользователя
        options.add_argument("--disable-blink-features=AutomationControlled")

        options.page_load_strategy = "eager"
        return options

    def get_driver(self):
        """Возвращает новый экземпляр драйвера с защитой от зависания при старте"""
        try:
            current_options = self.get_clean_options()

            # 🔥 Ставим жесткий таймаут запуска самого браузера (35 секунд)
            driver = uc.Chrome(options=current_options, startup_timeout=35)

            driver.set_page_load_timeout(35)
            return driver
        except Exception as e:
            logging.error(f"[Base Scraper] Ошибка создания драйвера Chrome: {e}")
            raise e
