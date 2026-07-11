# database/models.py
import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FlatListing(Base):
    __tablename__ = "flat_listings"

    id = Column(String, primary_key=True, index=True)
    source = Column(String, nullable=False)  # 'avito' или 'cian'
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
