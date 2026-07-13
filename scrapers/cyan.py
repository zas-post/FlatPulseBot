import logging
import time
import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

class CyanScraper(BaseScraper):
    def parse(self, url: str) -> list:
        """Парсинг Циан на основе универсального поиска целевых ссылок с фильтрацией по метро"""
        listings = []
        driver = None

        try:
            driver = self.get_driver()

            driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                },
            )

            logging.info("[Cyan Scraper] Открытие страницы Циан с маскировкой...")
            driver.get(url)

            time.sleep(7)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            all_links = soup.find_all("a", href=True)

            cyan_flat_links = []
            for a in all_links:
                href = a["href"]
                if "/flat/" in href and ("/rent/" in href or "/sale/" in href):
                    clean_href = href.split("?")[0]
                    full_url = (
                        clean_href
                        if clean_href.startswith("http")
                        else f"https://spb.cian.ru{clean_href}"
                    )

                    if full_url not in [x[0] for x in cyan_flat_links]:
                        cyan_flat_links.append((full_url, a))

            logging.info(
                f"[Cyan Scraper] Поиск по паттерну ссылок: найдено {len(cyan_flat_links)} уникальных предложений"
            )

            for item_url, link_element in cyan_flat_links:
                try:
                    parent_card = link_element.find_parent(
                        "div", class_=lambda c: c is not None
                    )

                    title = "Квартира на Циан"
                    price = "Цена по запросу"
                    skip_by_metro = False

                    if parent_card:
                        text_nodes = parent_card.find_all(string=True)

                        # 🔥 Фильтрация по времени до метро (> 15 минут)
                        for text in text_nodes:
                            t_clean = text.strip()
                            if "мин" in t_clean.lower():
                                minutes_match = re.search(r('(\d+)', t_clean)
                                if minutes_match:
                                    minutes = int(minutes_match.group(1))
                                    if minutes > 15:
                                        skip_by_metro = True
                                        break

                        if skip_by_metro:
                            logging.info(f"[Cyan Scraper] Пропуск объекта (далеко от метро: {item_url})")
                            continue

                        # Сбор заголовка
                        for text in text_nodes:
                            t_clean = text.strip()
                            if "кв." in t_clean or "м²" in t_clean:
                                title = t_clean
                                break

                        # Сбор цены
                        for text in text_nodes:
                            p_clean = text.strip()
                            if "₽" in p_clean or "руб" in p_clean:
                                price = (
                                    p_clean.replace("₽/мес.", "")
                                    .replace("₽", "")
                                    .strip()
                                )
                                break

                    id_match = re.search(r"/flat/(\d+)/", item_url)
                    item_id = id_match.group(1) if id_match else item_url

                    listings.append(
                        {
                            "id": item_id,
                            "title": title,
                            "price": price,
                            "url": item_url,
                        }
                    )
                except Exception as card_error:
                    logging.debug(
                        f"[Cyan Scraper] Ошибка разбора элемента: {card_error}"
                    )
                    continue

        except Exception as e:
            logging.error(f"[Cyan Scraper] Фатальная ошибка при парсинге страницы: {e}")
            raise e
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        return listings
