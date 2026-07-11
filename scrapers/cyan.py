import logging
import time
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class CyanScraper(BaseScraper):
    def parse(self, url: str) -> list:
        """Парсинг Циан на основе универсального поиска целевых ссылок"""
        listings = []
        driver = None

        try:
            driver = self.get_driver()

            # 🔥 МАСКИРОВКА: Подменяем User-Agent на человеческий, чтобы обойти базовый фрод Циана
            driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                },
            )

            logging.info("[Cyan Scraper] Открытие страницы Циан с маскировкой...")
            driver.get(url)

            # Даем скриптам Циан чуть больше времени (7 секунд) на прогрузку
            time.sleep(7)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # 🔥 УНИВЕРСАЛЬНЫЙ ПОДХОД: Ищем абсолютно все ссылки на странице
            all_links = soup.find_all("a", href=True)

            # Отбираем только те ссылки, которые ведут на карточки квартир (rent/flat или sale/flat)
            # Циан может использовать как полные, так и относительные ссылки
            cyan_flat_links = []
            for a in all_links:
                href = a["href"]
                if "/flat/" in href and ("/rent/" in href or "/sale/" in href):
                    # Очищаем ссылку от мусорных query-параметров отслеживания (?cdn=... и т.д.)
                    clean_href = href.split("?")[0]
                    full_url = (
                        clean_href
                        if clean_href.startswith("http")
                        else f"https://spb.cian.ru{clean_href}"
                    )

                    if full_url not in cyan_flat_links:
                        cyan_flat_links.append((full_url, a))

            logging.info(
                f"[Cyan Scraper] Поиск по паттерну ссылок: найдено {len(cyan_flat_links)} уникальных предложений"
            )

            # Собираем данные из найденных блоков ссылок
            for item_url, link_element in cyan_flat_links:
                try:
                    # Пытаемся найти заголовок и цену внутри родительского контейнера этой ссылки
                    # Поднимаемся на несколько уровней вверх к карточке
                    parent_card = link_element.find_parent(
                        "div", class_=lambda c: c is not None
                    )

                    title = "Квартира на Циан"
                    price = "Цена по запросу"

                    if parent_card:
                        # Ищем текст заголовка (обычно содержит "кв." или количество комнат/метраж)
                        text_nodes = parent_card.find_all(string=True)
                        for text in text_nodes:
                            t_clean = text.strip()
                            if "кв." in t_clean or "м²" in t_clean:
                                title = t_clean
                                break

                        # Ищем цену (ищем строку, где есть знак рубля или ₽)
                        for text in text_nodes:
                            p_clean = text.strip()
                            if "₽" in p_clean or "руб" in p_clean:
                                # Очищаем строку цены для красоты
                                price = (
                                    p_clean.replace("₽/мес.", "")
                                    .replace("₽", "")
                                    .strip()
                                )
                                break

                    listings.append({"title": title, "price": price, "url": item_url})
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
