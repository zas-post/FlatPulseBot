import logging
import random
import undetected_chromedriver as uc


class BaseScraper:
    def __init__(self):
        pass

    def get_clean_options(self):
        """Генерирует новый независимый объект настроек Chrome"""
        options = uc.ChromeOptions()

        # Основные настройки для стабильности работы Chrome внутри Docker-контейнера
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # 🚫 Отключаем картинки, чтобы снизить трафик и ускорить загрузку страниц
        options.add_argument("--blink-settings=imagesEnabled=false")

        # ⚡ Сверхлегкий режим: убираем всё тяжелое и ненужное, чтобы Авито не вешал систему
        options.add_argument("--disable-features=Translate,UserDataDirProfiles")
        options.add_argument("--num-raster-threads=2")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-remote-fonts")

        # 🪐 Изолируем порты отладки, чтобы процессы Авито и Циана не мешали друг другу
        random_port = random.randint(10000, 20000)
        options.add_argument(f"--remote-debugging-port={random_port}")

        # 🕵️ Маскировка под реального пользователя и очистка кэша
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-gpu")
        options.add_argument("--crash-dumps-dir=/tmp")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Загружаем только DOM-дерево (не дожидаемся загрузки всех тяжелых пикселей рекламы)
        options.page_load_strategy = "eager"
        return options

    def get_driver(self):
        """Возвращает новый экземпляр драйвера с жесткой привязкой к версии Chrome 150 и таймаутом 55 сек"""
        try:
            current_options = self.get_clean_options()

            # 🔥 startup_timeout=55 дает Docker-серверу время на инициализацию без вылета по ошибке
            # 🔥 version_main=150 решает проблему 'session not created' и гарантирует стабильную связь с Chrome 150
            driver = uc.Chrome(
                options=current_options, startup_timeout=55, version_main=150
            )

            # Ставим лимит в 55 секунд на загрузку самой страницы Авито/Циана
            driver.set_page_load_timeout(55)
            return driver
        except Exception as e:
            logging.error(f"[Base Scraper] Ошибка создания драйвера Chrome: {e}")
            raise e
