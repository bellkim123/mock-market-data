# App/models.py

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Platform(str, PyEnum):
    SMARTSTORE = "SMARTSTORE"
    COUPANG = "COUPANG"
    ZIGZAG = "ZIGZAG"
    ABLY = "ABLY"


class MockMarketOrder(Base):
    """
    mock_market_orders 테이블 매핑
    (이미 MariaDB에 생성된 DDL 기준)
    """

    __tablename__ = "mock_market_orders"

    mock_order_item_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # platform varchar(20)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # external_order_id varchar(50)
    external_order_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # external_order_item_id varchar(50)
    external_order_item_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # order_datetime datetime
    order_datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )

    # pay_datetime datetime
    pay_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # status_raw / status_normalized
    status_raw: Mapped[str] = mapped_column(String(50), nullable=False)
    status_normalized: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # 금액 관련
    product_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shipping_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_payment_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    pay_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # 상점/셀러 정보
    shop_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shop_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 구매자
    buyer_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    buyer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    buyer_tel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    buyer_email: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 수취인
    receiver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receiver_tel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    receiver_zipcode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    receiver_address1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receiver_address2: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 배송/송장
    delivery_company: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delivery_company_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    tracking_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 기타
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    memo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 원본 JSON (longtext, json_valid 체크)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
