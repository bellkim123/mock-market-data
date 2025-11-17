# App/main.py

from __future__ import annotations

from datetime import datetime, date, time
from datetime import date as _date_type
from typing import List

from .mock_data_generator import (
    generate_initial_mock_data,
    generate_hourly_new_orders,
    progress_order_statuses,
)

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import MockMarketOrder, Platform
from .market_responses import (
    to_smartstore_response,
    to_coupang_response,
    to_zigzag_response,
    to_ably_response,
)

app = FastAPI(title="Mock Market Orders API")


@app.on_event("startup")
def on_startup() -> None:
    """
    dev 환경에서만 테이블 자동 생성이 필요하면 주석 해제.
    이미 RDS에 mock_market_orders를 DDL로 만들어 두셨으면 굳이 호출 안하셔도 됩니다.
    """
    # Base.metadata.create_all(bind=engine)
    pass


# === API KEY 인증 ===

VALID_API_KEYS = {
    # "키값": "설명/사용자"
    "DEV-KEY-001": "data-engineer-1",
    "DEV-KEY-002": "data-engineer-2",
}


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    X-API-Key 헤더 필수.
    유효하지 않으면 401.
    """
    client_name = VALID_API_KEYS.get(x_api_key)
    if client_name is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return client_name  # 필요하면 로그 등에 사용 가능


# === 공통 조회 헬퍼 ===


def fetch_orders(
    db: Session,
    platform: Platform,
    limit: int,
    start_date: date | None,
    end_date: date | None,
) -> List[MockMarketOrder]:
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit는 1~1000 사이로 지정해주세요.")

    query = db.query(MockMarketOrder).filter(
        MockMarketOrder.platform == platform.value
    )

    # 날짜 필터: order_datetime 기준
    if start_date is not None:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(MockMarketOrder.order_datetime >= start_dt)

    if end_date is not None:
        end_dt = datetime.combine(end_date, time.max)
        query = query.filter(MockMarketOrder.order_datetime <= end_dt)

    orders: List[MockMarketOrder] = (
        query.order_by(MockMarketOrder.order_datetime.desc())
        .limit(limit)
        .all()
    )
    return orders


# === Health Check ===


@app.get("/")
async def root() -> dict:
    return {"message": "mock-market-api running"}


# === 플랫폼별 API ===
# 공통: 헤더 X-API-Key 필요
# 날짜 파라미터 예시:
#   /coupang/orders?start_date=2025-01-15&end_date=2025-01-15&limit=50


@app.get("/smartstore/orders")
def get_smartstore_orders(
    limit: int = 50,
    start_date: date | None = Query(
        None, description="조회 시작일 (YYYY-MM-DD, 예: 2025-10-23)"
    ),
    end_date: date | None = Query(
        None, description="조회 종료일 (YYYY-MM-DD, 예: 2025-10-24)"
    ),
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    orders = fetch_orders(db, Platform.SMARTSTORE, limit, start_date, end_date)
    return to_smartstore_response(orders)


@app.get("/coupang/orders")
def get_coupang_orders(
    limit: int = 50,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    orders = fetch_orders(db, Platform.COUPANG, limit, start_date, end_date)
    return to_coupang_response(orders)


@app.get("/zigzag/orders")
def get_zigzag_orders(
    limit: int = 50,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    orders = fetch_orders(db, Platform.ZIGZAG, limit, start_date, end_date)
    return to_zigzag_response(orders)


@app.get("/ably/orders")
def get_ably_orders(
    limit: int = 50,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    orders = fetch_orders(db, Platform.ABLY, limit, start_date, end_date)
    return to_ably_response(orders)

@app.post("/admin/mock/initial")
def admin_generate_initial_mock_data(
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """
    2025-10-01 ~ 2025-11-18 구간 전체에 대한 초기 mock 데이터 생성
    - 너무 많으면 orders_per_hour_per_platform 조절
    """
    # 필요하면 특정 키만 허용
    # if client != "data-engineer-1":
    #     raise HTTPException(status_code=403, detail="Not allowed")

    inserted = generate_initial_mock_data(
        db,
        start_date=_date_type(2025, 10, 1),
        end_date=_date_type(2025, 11, 18),
        orders_per_hour_per_platform=3,
    )
    return {"inserted": inserted}


@app.post("/admin/mock/hourly-insert")
def admin_generate_hourly_insert(
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """
    현재 시각 기준 한 시간 구간에 대해, 플랫폼별 새 주문 삽입
    """
    inserted = generate_hourly_new_orders(db)
    return {"inserted": inserted}


@app.post("/admin/mock/hourly-update")
def admin_progress_order_statuses(
    client: str = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """
    아직 종단 상태가 아닌 주문들 일부를 다음 단계 상태로 진행
    """
    updated = progress_order_statuses(db)
    return {"updated": updated}