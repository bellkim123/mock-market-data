from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Enum, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Market(str, PyEnum):
    SMARTSTORE = "SMARTSTORE"
    COUPANG = "COUPANG"
    ELEVENST = "ELEVENST"
    ABLY = "ABLY"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    market: Mapped[Market] = mapped_column(Enum(Market), index=True, nullable=False)
    order_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    order_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    buyer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
