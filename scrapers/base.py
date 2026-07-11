# scrapers/base.py
import random
import undetected_chromedriver as uc


class BaseScraper:
    def _get_clean_options(self):
        """Генерирует НОВЫЙ объект опций при каждом запросе браузера"""
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "--blink-settings=imagesEnabled=false"
        )  # Отключаем картинки
        options.page_load_strategy = "eager"  # Стратегия eager против таймаутов

        # Маскировка под случайные разрешения экранов
        resolutions = ["1920,1080", "1440,900", "1536,864", "1366,768"]
        options.add_argument(f"--window-size={random.choice(resolutions)}")
        return options

    def get_driver(self):
        """Создает драйвер со свежими опциями"""
        options = self._get_clean_options()
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        return driver
