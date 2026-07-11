# database/connection.py
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from database.models import Base

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_context():
    """Контекстный менеджер для безопасной работы с сессиями БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def filter_new_listings(listings, source="avito") -> list:
    """Безопасная фильтрация дубликатов"""
    from database.models import FlatListing

    new_listings = []
    seen_ids = set()

    with get_db_context() as db:
        for item in listings:
            item_id = item["id"]
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            exists = (
                db.query(FlatListing)
                .filter(FlatListing.id == item_id, FlatListing.source == source)
                .first()
            )

            if not exists:
                db_item = FlatListing(
                    id=item_id,
                    source=source,
                    title=item["title"],
                    price=item["price"],
                    url=item["url"],
                )
                db.add(db_item)
                new_listings.append(item)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return new_listings
