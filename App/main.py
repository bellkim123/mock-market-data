# App/main.py
from __future__ import annotations
from pathlib import Path

from datetime import datetime, date, time
from datetime import date as _date_type
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from .mock_data_generator import (
    generate_initial_mock_data,
    generate_hourly_new_orders,
    progress_order_statuses,
)
from .database import Base, engine, get_db
from .models import MockMarketOrder, Platform, MockApiClient
from .market_responses import (
    to_smartstore_response,
    to_coupang_response,
    to_zigzag_response,
    to_ably_response,
)
DOC_PATH = Path(__file__).parent.parent / "docs" / "onboarding.md"
APP_DESCRIPTION = DOC_PATH.read_text(encoding="utf-8")

app = FastAPI(
    title="Mock Market Orders API")

@app.on_event("startup")
def on_startup() -> None:
    """
    dev 환경에서만 테이블 자동 생성이 필요하면 주석 해제.
    이미 RDS에 mock_market_orders / mock_api_clients 를 DDL로 만들어 두셨으면
    굳이 호출 안하셔도 됩니다.
    """
    # Base.metadata.create_all(bind=engine)
    pass


# === API KEY 인증 (DB 기반) ===


def require_api_client(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> MockApiClient:
    """
    X-API-Key 헤더 필수.
    mock_api_clients 테이블에서 활성화된 키인지 확인.
    - 없거나 비활성화면 401
    """
    client: MockApiClient | None = (
        db.query(MockApiClient)
        .filter(
            MockApiClient.api_key == x_api_key,
            MockApiClient.is_active.is_(True),
        )
        .first()
    )

    if client is None:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    # (옵션) 여기에서 rate limit / 토큰 버킷 체크 로직 추가 가능
    return client


# === 공통 조회 헬퍼 ===


def fetch_orders(
    db: Session,
    platform: Platform,
    seller_id: int,
    page: int,
    page_size: int,
    start_date: date | None,
    end_date: date | None,
) -> List[MockMarketOrder]:
    """
    페이지네이션:
    - page: 1부터 시작
    - page_size: 페이지당 건수 (1~100)
    """
    if page <= 0:
        raise HTTPException(status_code=400, detail="page는 1 이상이어야 합니다.")
    if page_size <= 0 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="page_size는 1~100 사이로 지정해주세요.",
        )

    query = db.query(MockMarketOrder).filter(
        MockMarketOrder.platform == platform.value,
        MockMarketOrder.seller_id == seller_id,
    )

    # 날짜 필터: order_datetime 기준
    if start_date is not None:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(MockMarketOrder.order_datetime >= start_dt)

    if end_date is not None:
        end_dt = datetime.combine(end_date, time.max)
        query = query.filter(MockMarketOrder.order_datetime <= end_dt)

    offset = (page - 1) * page_size

    orders: List[MockMarketOrder] = (
        query.order_by(MockMarketOrder.order_datetime.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return orders


# === Health Check ===


@app.get("/",include_in_schema=False)
async def root() -> dict:
    return {"message": "mock-market-api running"}


# === 플랫폼별 API ===
# 공통: 헤더 X-API-Key 필요
# 날짜 파라미터 예시:
#   /coupang/orders?start_date=2025-01-15&end_date=2025-01-15&page=1&page_size=50


@app.get("/smartstore/orders")
def get_smartstore_orders(
    page: int = Query(
        1,
        ge=1,
        description="페이지 번호 (1부터 시작)",
    ),
    page_size: int = Query(
        50,
        ge=1,
        le=100,
        description="페이지당 주문 건수 (1~100, 기본값 50)",
    ),
    start_date: date | None = Query(
        None, description="조회 시작일 (YYYY-MM-DD, 예: 2025-10-23)"
    ),
    end_date: date | None = Query(
        None, description="조회 종료일 (YYYY-MM-DD, 예: 2025-10-24)"
    ),
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    # API Key가 SMARTSTORE 전용인지 검증
    if client.platform != Platform.SMARTSTORE.value:
        raise HTTPException(
            status_code=403,
            detail="This client cannot access SMARTSTORE data.",
        )

    orders = fetch_orders(
        db,
        Platform.SMARTSTORE,
        client.seller_id,
        page,
        page_size,
        start_date,
        end_date,
    )
    return to_smartstore_response(orders)


@app.get("/coupang/orders")
def get_coupang_orders(
    page: int = Query(
        1,
        ge=1,
        description="페이지 번호 (1부터 시작)",
    ),
    page_size: int = Query(
        50,
        ge=1,
        le=100,
        description="페이지당 주문 건수 (1~100, 기본값 50)",
    ),
    start_date: date | None = Query(
        None,
        description="조회 시작일 (YYYY-MM-DD)",
    ),
    end_date: date | None = Query(
        None,
        description="조회 종료일 (YYYY-MM-DD)",
    ),
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    if client.platform != Platform.COUPANG.value:
        raise HTTPException(
            status_code=403,
            detail="This client cannot access COUPANG data.",
        )

    orders = fetch_orders(
        db,
        Platform.COUPANG,
        client.seller_id,
        page,
        page_size,
        start_date,
        end_date,
    )
    return to_coupang_response(orders)


@app.get("/zigzag/orders")
def get_zigzag_orders(
    page: int = Query(
        1,
        ge=1,
        description="페이지 번호 (1부터 시작)",
    ),
    page_size: int = Query(
        50,
        ge=1,
        le=100,
        description="페이지당 주문 건수 (1~100, 기본값 50)",
    ),
    start_date: date | None = Query(
        None,
        description="조회 시작일 (YYYY-MM-DD)",
    ),
    end_date: date | None = Query(
        None,
        description="조회 종료일 (YYYY-MM-DD)",
    ),
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    if client.platform != Platform.ZIGZAG.value:
        raise HTTPException(
            status_code=403,
            detail="This client cannot access ZIGZAG data.",
        )

    orders = fetch_orders(
        db,
        Platform.ZIGZAG,
        client.seller_id,
        page,
        page_size,
        start_date,
        end_date,
    )
    return to_zigzag_response(orders)


@app.get("/ably/orders")
def get_ably_orders(
    page: int = Query(
        1,
        ge=1,
        description="페이지 번호 (1부터 시작)",
    ),
    page_size: int = Query(
        50,
        ge=1,
        le=100,
        description="페이지당 주문 건수 (1~100, 기본값 50)",
    ),
    start_date: date | None = Query(
        None,
        description="조회 시작일 (YYYY-MM-DD)",
    ),
    end_date: date | None = Query(
        None,
        description="조회 종료일 (YYYY-MM-DD)",
    ),
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    if client.platform != Platform.ABLY.value:
        raise HTTPException(
            status_code=403,
            detail="This client cannot access ABLY data.",
        )

    orders = fetch_orders(
        db,
        Platform.ABLY,
        client.seller_id,
        page,
        page_size,
        start_date,
        end_date,
    )
    return to_ably_response(orders)


# === Admin Mock 데이터 생성/업데이트 ===

@app.post("/admin/mock/initial")
def admin_generate_initial_mock_data(
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    """
    2025-10-01 ~ 2025-11-18 구간 전체에 대한 초기 mock 데이터 생성
    - 너무 많으면 orders_per_hour_per_platform 조절
    - 전체 셀러(1~100) 대상으로 랜덤 분배
    """
    # 필요하면 특정 셀러 또는 내부용 키만 허용
    # if client.seller_id != 1:
    #     raise HTTPException(status_code=403, detail="Not allowed")

    inserted = generate_initial_mock_data(
        db,
        start_date=_date_type(2025, 10, 1),
        end_date=_date_type(2025, 11, 18),
        orders_per_hour_per_platform=100,
    )
    return {"inserted": inserted}


@app.post("/admin/mock/hourly-insert",include_in_schema=False)
def admin_generate_hourly_insert(
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    """
    현재 시각 기준 한 시간 구간에 대해, 플랫폼별 새 주문 삽입
    - 전체 셀러(1~100) 대상으로 랜덤 분배
    """
    inserted = generate_hourly_new_orders(db)
    return {"inserted": inserted}


@app.post("/admin/mock/hourly-update",include_in_schema=False)
def admin_progress_order_statuses(
    client: MockApiClient = Depends(require_api_client),
    db: Session = Depends(get_db),
):
    """
    아직 종단 상태가 아닌 주문들 일부를 다음 단계 상태로 진행
    """
    updated = progress_order_statuses(db)
    return {"updated": updated}
