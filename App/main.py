from datetime import datetime
import random
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Order, Market
from .market_responses import to_market_response

app = FastAPI(title="Mock Market Orders API")


@app.on_event("startup")
def on_startup() -> None:
    # RDS에 orders 테이블 없으면 생성
    Base.metadata.create_all(bind=engine)


# === Mock 데이터 생성 유틸 ===

BUYER_NAMES = ["홍길동", "김철수", "이영희", "박영수", "최민수"]
ITEM_NAMES = ["양말", "티셔츠", "에코백", "머그컵", "키보드", "마우스"]


def create_random_order(db: Session, market: Market) -> Order:
    buyer_name = random.choice(BUYER_NAMES)
    item_name = random.choice(ITEM_NAMES)
    qty = random.randint(1, 5)
    unit_price = random.choice([5000, 10000, 15000, 20000])
    total_price = qty * unit_price

    order = Order(
        market=market,
        order_id=f"{market.value[:2]}-{int(datetime.utcnow().timestamp())}-{random.randint(1000, 9999)}",
        order_datetime=datetime.utcnow(),
        buyer_name=buyer_name,
        item_name=item_name,
        qty=qty,
        unit_price=unit_price,
        total_price=total_price,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.get("/")
async def root():
    return {"message": "mock-market-api running"}


@app.post("/admin/generate-mock")
def generate_mock_data(db: Session = Depends(get_db)):
    """
    각 마켓별로 5건씩 랜덤 주문 생성
    """
    for market in Market:
        for _ in range(5):
            create_random_order(db, market)
    return {"message": "mock data generated"}


@app.get("/mock/{market}/orders")
def get_market_orders(
    market: Market,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    /mock/SMARTSTORE/orders
    /mock/COUPANG/orders ...
    """
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit는 1~1000 사이로 지정해주세요.")

    orders: List[Order] = (
        db.query(Order)
        .filter(Order.market == market)
        .order_by(Order.order_datetime.desc())
        .limit(limit)
        .all()
    )

    return to_market_response(market, orders)
