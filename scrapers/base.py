import logging
import undetected_chromedriver as uc


class BaseScraper:
    def __init__(self):
        # В инициализаторе ничего не храним, чтобы объект настроек не дублировался
        pass

    def get_clean_options(self):
        """Каждый раз генерирует абсолютно новый и независимый объект настроек Chrome"""
        options = uc.ChromeOptions()

        # Бронированные настройки для стабильности внутри Docker контейнера
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--blink-settings=imagesEnabled=false")

        # Стратегия ленивой загрузки
        options.page_load_strategy = "eager"
        return options

    def get_driver(self):
        """Возвращает новый экземпляр драйвера со свежими настройками"""
        try:
            # Вызываем создание новых настроек при каждом открытии браузера
            current_options = self.get_clean_options()
            driver = uc.Chrome(options=current_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logging.error(f"[Base Scraper] Ошибка создания драйвера Chrome: {e}")
            raise e
