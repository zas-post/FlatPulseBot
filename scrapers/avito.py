import time
import random
import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers.base import BaseScraper


class AvitoScraper(BaseScraper):
    def _execute_parsing(self, search_url) -> list:
        driver = self.get_driver()
        listings = []
        try:
            logging.info("[Avito Scraper] Открытие страницы...")

            # Имитируем реальный переход: сначала заходим на главную Авито, чтобы получить базовые куки
            try:
                driver.get("https://www.avito.ru")
                time.sleep(random.uniform(1.5, 3.0))
            except Exception:
                pass  # Если главная не отвечает, не страшно, идем дальше

            # Теперь переходим на саму целевую страницу поиска
            driver.get(search_url)

            # Даем странице физически "отстояться" и подгрузить скрипты маскировки
            time.sleep(random.uniform(4.0, 7.0))

            # Ожидание контейнера выдачи (увеличили таймаут до 25 секунд для стабильности)
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@data-marker='catalog-serp']")
                )
            )

            # Плавная имитация чтения страницы человеком перед парсингом
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 5);")
            time.sleep(random.uniform(2.0, 3.5))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("div", {"data-marker": "item"})

            for item in items:
                try:
                    title_tag = item.find("a", {"data-marker": "item-title"})
                    if not title_tag:
                        continue

                    title = title_tag.text.strip()
                    href = title_tag["href"]
                    url = (
                        f"https://www.avito.ru{href}" if href.startswith("/") else href
                    )

                    price_tag = item.find("meta", {"itemprop": "price"})
                    price = price_tag["content"] if price_tag else "Цена не указана"

                    item_id = item.get("data-item-id", url.split("_")[-1])

                    listings.append(
                        {
                            "id": str(item_id),
                            "title": title,
                            "price": f"{int(price):,}" if price.isdigit() else price,
                            "url": url,
                        }
                    )
                except Exception:
                    continue
        finally:
            if driver:
                driver.quit()

        return listings

    def parse(self, search_url, max_retries=3) -> list:
        for attempt in range(1, max_retries + 1):
            try:
                result = self._execute_parsing(search_url)
                if result:
                    return result
                logging.warning(
                    f"[Avito Scraper] Попытка {attempt}: Страница открылась, но объявлений не найдено."
                )
            except Exception as e:
                logging.error(f"[Avito Scraper] Ошибка на попытке {attempt}: {e}")

            if attempt < max_retries:
                # Увеличиваем паузу между ретраями, чтобы IP "остыл"
                sleep_time = attempt * 20
                logging.info(
                    f"[Avito Scraper] Ожидание {sleep_time} сек перед попыткой {attempt + 1}..."
                )
                time.sleep(sleep_time)
        return []
