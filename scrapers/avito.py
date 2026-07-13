import time
import random
import logging
import re
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
            driver.get(search_url)

            # Ожидание контейнера выдачи
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@data-marker='catalog-serp']")
                )
            )

            time.sleep(random.uniform(2.0, 4.0))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 4);")

            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("div", {"data-marker": "item"})

            for item in items:
                try:
                    # 🔥 Фильтрация рекомендаций по времени до метро (> 15 минут)
                    item_text = item.get_text()
                    metro_time_match = re.search(
                        r"(?:от\s+)?(\d+)\s*мин", item_text, re.IGNORECASE
                    )
                    if metro_time_match:
                        minutes = int(metro_time_match.group(1))
                        if minutes > 15:
                            logging.info(
                                f"[Avito Scraper] Пропуск объекта (далеко от метро: {minutes} мин)"
                            )
                            continue

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
            driver.quit()

        return listings

    def parse(self, search_url, max_retries=3) -> list:
        for attempt in range(1, max_retries + 1):
            try:
                result = self._execute_parsing(search_url)
                if result:
                    return result
            except Exception as e:
                logging.error(f"[Avito Scraper] Ошибка на попытке {attempt}: {e}")
                if attempt < max_retries:
                    time.sleep(attempt * 10)
        return []
