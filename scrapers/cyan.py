import logging
import time
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class CyanScraper(BaseScraper):
    def parse(self, url: str) -> list:
        """Парсинг первой страницы фильтра Циан с обходом таймаутов"""
        listings = []
        driver = None

        try:
            driver = self.get_driver()
            logging.info("[Cyan Scraper] Открытие страницы Циан...")
            driver.get(url)

            # Даем скриптам Циан 5 секунд на подгрузку динамического контента
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Находим карточки объявлений (Циан использует тег article для предложений)
            cards = soup.find_all("article", data_name="CardComponent")

            if not cards:
                # Резервный поиск по подстроке классов, если Циан обновит data-атрибуты
                cards = soup.find_all("div", class_=lambda c: c and "general-card" in c)

            # 🔥 Лог для диагностики: проверяем, видит ли браузер квартиры на странице
            logging.info(
                f"[Cyan Scraper] Найдено {len(cards)} карточек на странице Циан"
            )

            for card in cards:
                try:
                    # 1. Поиск ссылки и заголовка
                    link_element = card.find(
                        "a", class_=lambda c: c and "header" in c
                    ) or card.find("a")
                    if not link_element or "href" not in link_element.attrs:
                        continue

                    href = link_element["href"]
                    # Исправляем относительные ссылки, если они есть
                    item_url = (
                        href
                        if href.startswith("http")
                        else f"https://spb.cian.ru{href}"
                    )

                    # Заголовок (например, "2-комн. кв., 56 м²")
                    title_element = (
                        card.find("span", data_mark="OfferTitle") or link_element
                    )
                    title = (
                        title_element.get_text(strip=True)
                        if title_element
                        else "Квартира на Циан"
                    )

                    # 2. Поиск цены
                    price_element = card.find(
                        "span", data_mark="MainPrice"
                    ) or card.find("span", class_=lambda c: c and "price" in c)
                    price = (
                        price_element.get_text(strip=True)
                        if price_element
                        else "Цена по запросу"
                    )

                    # Очищаем цену от лишних символов для красоты
                    price = price.replace("₽/мес.", "").replace("₽", "").strip()

                    listings.append({"title": title, "price": price, "url": item_url})
                except Exception as card_error:
                    logging.debug(
                        f"[Cyan Scraper] Ошибка разбора отдельной карточки: {card_error}"
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
