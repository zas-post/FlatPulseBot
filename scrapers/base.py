import logging
import undetected_chromedriver as uc


class BaseScraper:
    def __init__(self):
        self.options = uc.ChromeOptions()

        # 🔥 КРИТИЧЕСКИЕ НАСТРОЙКИ ДЛЯ СТАБИЛЬНОСТИ В DOCKER
        self.options.add_argument(
            "--headless=new"
        )  # Запуск без графического окна (важно для Linux/Docker)
        self.options.add_argument(
            "--no-sandbox"
        )  # Разрешаем запуск под root-пользователем в контейнере
        self.options.add_argument(
            "--disable-dev-shm-usage"
        )  # Используем общую память диска вместо /dev/shm (защита от вылета по памяти)
        self.options.add_argument(
            "--blink-settings=imagesEnabled=false"
        )  # Отключаем картинки для ускорения загрузки и экономии трафика

        # Защита от зависания рендерера страницы
        self.options.page_load_strategy = "eager"

    def get_driver(self):
        """Возвращает новый чистый экземпляр драйвера"""
        try:
            # На сервере всегда используем headless
            driver = uc.Chrome(options=self.options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logging.error(f"[Base Scraper] Ошибка создания драйвера Chrome: {e}")
            raise e
