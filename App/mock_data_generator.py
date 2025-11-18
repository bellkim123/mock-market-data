# App/mock_data_generator.py

from __future__ import annotations

import json
import random
from datetime import datetime, date, time, timedelta
from typing import List

from sqlalchemy.orm import Session

from .models import MockMarketOrder, Platform

# ===== 공통 정규화 상태 플로우 =====
# - 초기 Insert: PAID / PREPARING_SHIPMENT / SHIPPED / DELIVERED / CANCELLED 중 하나
# - Update 배치: PAID -> PREPARING_SHIPMENT -> SHIPPED -> DELIVERED
NORMALIZED_STATUS_FLOW: dict[str, str] = {
    "PAID": "PREPARING_SHIPMENT",
    "PREPARING_SHIPMENT": "SHIPPED",
    "SHIPPED": "DELIVERED",
}

# ===== 플랫폼별 raw 상태 값 =====
PLATFORM_STATUS_CHOICES: dict[Platform, dict[str, List[str]]] = {
    Platform.SMARTSTORE: {
        "PAID": ["결제완료"],
        "PREPARING_SHIPMENT": ["상품준비중"],
        "SHIPPED": ["배송중"],
        "DELIVERED": ["배송완료", "구매확정"],
        "CANCELLED": ["주문취소", "결제취소"],
    },
    Platform.COUPANG: {
        "PAID": ["ACCEPT"],
        "PREPARING_SHIPMENT": ["INSTRUCT"],
        "SHIPPED": ["IN_DELIVERY"],
        "DELIVERED": ["FINAL_DELIVERY"],
        "CANCELLED": ["CANCELED"],
    },
    Platform.ZIGZAG: {
        "PAID": ["PAY_COMPLETE"],
        "PREPARING_SHIPMENT": ["DELIVERY_READY"],
        "SHIPPED": ["DELIVERY_IN_PROGRESS"],
        "DELIVERED": ["DELIVERY_COMPLETED"],
        "CANCELLED": ["ORDER_CANCEL"],
    },
    Platform.ABLY: {
        "PAID": ["결제완료"],
        "PREPARING_SHIPMENT": ["배송준비중"],
        "SHIPPED": ["배송중"],
        "DELIVERED": ["배송완료"],
        "CANCELLED": ["취소완료"],
    },
}

# ===== 플랫폼별 택배사 / 코드 (의도적으로 제각각) =====
PLATFORM_DELIVERY_COMPANIES: dict[Platform, List[tuple[str, str]]] = {
    Platform.SMARTSTORE: [
        ("CJ대한통운", "CJGLS"),
        ("롯데택배", "LOTTES"),
        ("한진택배", "HANJIN"),
    ],
    Platform.COUPANG: [
        ("쿠팡로지스틱스", "CPLG"),
        ("CJ대한통운", "CJP"),
    ],
    Platform.ZIGZAG: [
        ("로젠택배", "LOGEN_ZZ"),
        ("CJ대한통운", "CJ_ZZ"),
    ],
    Platform.ABLY: [
        ("우체국택배", "KOREAPOST_AB"),
        ("CJ대한통운", "CJ_AB"),
    ],
}

BUYER_NAMES = ["김철수", "이영희", "박민수", "정유진", "홍길동"]
SHOP_NAMES = ["위시어스", "팔랑샵", "데일리룩", "커피굿즈샵"]
PAY_METHODS = ["CARD", "KAKAO_PAY", "NAVER_PAY", "TOSS_PAY", "무통장입금"]
MEMOS = [
    "문 앞에 두고 가주세요.",
    "경비실에 맡겨주세요.",
    "부재 시 연락 부탁드립니다.",
    "빠른 배송 부탁드려요.",
]

MIN_SELLER_ID = 1
MAX_SELLER_ID = 100  # mock_api_clients.seller_id 범위와 맞춰 사용


def _choose_status(platform: Platform) -> tuple[str, str]:
    """
    플랫폼별 raw / normalized 상태 1쌍 선택
    """
    status_map = PLATFORM_STATUS_CHOICES[platform]
    normalized = random.choice(list(status_map.keys()))  # PAID, PREPARING_SHIPMENT, ...
    raw = random.choice(status_map[normalized])
    return raw, normalized


def _next_status(platform: Platform, current_normalized: str) -> tuple[str, str] | None:
    """
    배치 업데이트용: 현재 정규화 상태에서 다음 정규화 상태 + raw 상태 리턴
    종단 상태(DELIVERED, CANCELLED 등)는 None 리턴
    """
    if current_normalized not in NORMALIZED_STATUS_FLOW:
        return None

    next_normalized = NORMALIZED_STATUS_FLOW[current_normalized]
    raw_candidates = PLATFORM_STATUS_CHOICES[platform].get(next_normalized)
    if not raw_candidates:
        return None

    return random.choice(raw_candidates), next_normalized


def _choose_delivery_company(platform: Platform) -> tuple[str, str]:
    candidates = PLATFORM_DELIVERY_COMPANIES[platform]
    return random.choice(candidates)


def _generate_external_ids(
    platform: Platform,
    base_dt: datetime,
    seq: int,
) -> tuple[str, str]:
    """
    플랫폼별 주문번호/주문아이템번호 포맷을 적당히 다르게 생성
    """
    ymdh = base_dt.strftime("%Y%m%d%H")

    if platform == Platform.COUPANG:
        order_id = f"2{ymdh}{seq:04d}"  # 예: 2202510180001
        item_id = f"{order_id}{seq:02d}"  # 예: 220251018000101
    elif platform == Platform.SMARTSTORE:
        order_id = f"{ymdh}-{seq:04d}"  # 예: 20251018-0001
        item_id = f"{order_id}-P{seq:02d}"  # 예: 20251018-0001-P01
    elif platform == Platform.ZIGZAG:
        order_id = f"ZZ{ymdh}{seq:04d}"
        item_id = f"ZZIT{ymdh}{seq:06d}"
    elif platform == Platform.ABLY:
        order_id = f"AB{ymdh}{seq:04d}"
        item_id = f"{seq}"
    else:
        order_id = f"{ymdh}{seq:04d}"
        item_id = f"{ymdh}{seq:06d}"

    return order_id, item_id


def _generate_tracking_number(platform: Platform, base_dt: datetime, seq: int) -> str:
    prefix = {
        Platform.SMARTSTORE: "CJ",
        Platform.COUPANG: "CP",
        Platform.ZIGZAG: "ZZ",
        Platform.ABLY: "AB",
    }.get(platform, "TRK")

    return f"{prefix}{base_dt.strftime('%m%d')}{random.randint(1000000, 9999999)}"


def _random_phone() -> str:
    return f"010-{random.randint(1000, 9999):04d}-{random.randint(1000, 9999):04d}"


def _build_raw_payload(platform: Platform, order_dict: dict) -> str:
    """
    raw_payload에 저장할 JSON (간단 통합 포맷)
    - 실제 플랫폼 원본과 1:1은 아니지만, ETL 연습용 "raw"라고 생각하시면 됩니다.
    """
    payload = {
        "platform": platform.value,
        "external_order_id": order_dict["external_order_id"],
        "external_order_item_id": order_dict["external_order_item_id"],
        "status": {
            "raw": order_dict["status_raw"],
            "normalized": order_dict["status_normalized"],
        },
        "amount": {
            "product_amount": order_dict["product_amount"],
            "shipping_fee": order_dict["shipping_fee"],
            "discount_amount": order_dict["discount_amount"],
            "total_payment_amount": order_dict["total_payment_amount"],
            "currency": order_dict["currency"],
        },
        "buyer": {
            "buyer_id": order_dict["buyer_id"],
            "buyer_name": order_dict["buyer_name"],
            "buyer_tel": order_dict["buyer_tel"],
            "buyer_email": order_dict["buyer_email"],
        },
        "receiver": {
            "receiver_name": order_dict["receiver_name"],
            "receiver_tel": order_dict["receiver_tel"],
            "receiver_zipcode": order_dict["receiver_zipcode"],
            "receiver_address1": order_dict["receiver_address1"],
            "receiver_address2": order_dict["receiver_address2"],
        },
        "shipping": {
            "delivery_company": order_dict["delivery_company"],
            "delivery_company_code": order_dict["delivery_company_code"],
            "tracking_number": order_dict["tracking_number"],
        },
        "meta": {
            "order_datetime": order_dict["order_datetime"].isoformat(),
            "pay_datetime": order_dict["pay_datetime"].isoformat()
            if order_dict["pay_datetime"]
            else None,
            "country": order_dict["country"],
            "memo": order_dict["memo"],
        },
    }

    return json.dumps(payload, ensure_ascii=False)


def _create_mock_order(
    db: Session,
    platform: Platform,
    order_datetime: datetime,
    global_seq: int,
    seller_id: int,
) -> MockMarketOrder:
    """
    한 건의 MockMarketOrder 인스턴스를 생성해서 세션에 add
    """
    shop_name = random.choice(SHOP_NAMES)
    buyer_name = random.choice(BUYER_NAMES)
    buyer_tel = _random_phone()
    receiver_name = random.choice([buyer_name, "배송수령인"])
    receiver_tel = _random_phone()

    status_raw, status_normalized = _choose_status(platform)
    quantity = random.randint(1, 3)
    product_amount = random.randint(5000, 50000)
    shipping_fee = random.choice([0, 0, 3000])  # 무료가 조금 더 자주 나오게
    discount_amount = random.choice([0, 0, 0, int(product_amount * 0.1)])
    total_payment_amount = product_amount * quantity + shipping_fee - discount_amount

    pay_datetime = None
    if status_normalized in ("PAID", "PREPARING_SHIPMENT", "SHIPPED", "DELIVERED"):
        # 주문 0~120분 사이에 결제된 것으로
        pay_datetime = order_datetime + timedelta(
            minutes=random.randint(0, 120)
        )

    # 플랫폼별 택배사/코드, 아직 출고 전이면 비워둘 수도 있음
    delivery_company = None
    delivery_company_code = None
    tracking_number = None
    if status_normalized in ("SHIPPED", "DELIVERED"):
        delivery_company, delivery_company_code = _choose_delivery_company(
            platform
        )
        tracking_number = _generate_tracking_number(
            platform, order_datetime, global_seq
        )

    external_order_id, external_order_item_id = _generate_external_ids(
        platform, order_datetime, global_seq
    )

    order_dict = {
        "seller_id": seller_id,
        "platform": platform.value,
        "external_order_id": external_order_id,
        "external_order_item_id": external_order_item_id,
        "order_datetime": order_datetime,
        "pay_datetime": pay_datetime,
        "status_raw": status_raw,
        "status_normalized": status_normalized,
        "product_amount": product_amount,
        "shipping_fee": shipping_fee,
        "discount_amount": discount_amount,
        "total_payment_amount": total_payment_amount,
        "pay_method": random.choice(PAY_METHODS),
        "currency": "KRW",
        "shop_id": f"SHOP-{platform.value[:2]}-{random.randint(1, 50):03d}",
        "shop_name": shop_name,
        "buyer_id": f"user_{random.randint(1000, 9999)}",
        "buyer_name": buyer_name,
        "buyer_tel": buyer_tel,
        "buyer_email": f"mock{random.randint(1, 9999)}@example.com",
        "receiver_name": receiver_name,
        "receiver_tel": receiver_tel,
        "receiver_zipcode": f"{random.randint(10000, 99999)}",
        "receiver_address1": "서울특별시 테스트구 테스트로 123",
        "receiver_address2": "테스트아파트 101동 1001호",
        "delivery_company": delivery_company,
        "delivery_company_code": delivery_company_code,
        "tracking_number": tracking_number,
        "quantity": quantity,
        "country": "KR",
        "memo": random.choice(MEMOS),
    }

    raw_payload = _build_raw_payload(platform, order_dict)

    order = MockMarketOrder(
        seller_id=order_dict["seller_id"],
        platform=order_dict["platform"],
        external_order_id=order_dict["external_order_id"],
        external_order_item_id=order_dict["external_order_item_id"],
        order_datetime=order_dict["order_datetime"],
        pay_datetime=order_dict["pay_datetime"],
        status_raw=order_dict["status_raw"],
        status_normalized=order_dict["status_normalized"],
        product_amount=order_dict["product_amount"],
        shipping_fee=order_dict["shipping_fee"],
        discount_amount=order_dict["discount_amount"],
        total_payment_amount=order_dict["total_payment_amount"],
        pay_method=order_dict["pay_method"],
        currency=order_dict["currency"],
        shop_id=order_dict["shop_id"],
        shop_name=order_dict["shop_name"],
        buyer_id=order_dict["buyer_id"],
        buyer_name=order_dict["buyer_name"],
        buyer_tel=order_dict["buyer_tel"],
        buyer_email=order_dict["buyer_email"],
        receiver_name=order_dict["receiver_name"],
        receiver_tel=order_dict["receiver_tel"],
        receiver_zipcode=order_dict["receiver_zipcode"],
        receiver_address1=order_dict["receiver_address1"],
        receiver_address2=order_dict["receiver_address2"],
        delivery_company=order_dict["delivery_company"],
        delivery_company_code=order_dict["delivery_company_code"],
        tracking_number=order_dict["tracking_number"],
        quantity=order_dict["quantity"],
        country=order_dict["country"],
        memo=order_dict["memo"],
        raw_payload=raw_payload,
    )

    db.add(order)
    return order


# ========================
# 1) 초기 풀 구간 더미데이터 생성
# ========================
def generate_initial_mock_data(
    db: Session,
    start_date: date,
    end_date: date,
    orders_per_hour_per_platform: int = 10,
    seed: int | None = 42,
) -> int:
    """
    10월 1일 ~ 11월 18일 사이 전체 구간에 대해
    - 모든 플랫폼별로
    - 시간 단위로
    - orders_per_hour_per_platform 개씩 주문 생성
    - 각 주문은 seller_id (1~100) 중 랜덤 한 셀러에 귀속
    """
    if seed is not None:
        random.seed(seed)

    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    current = start_dt
    inserted = 0
    global_seq = 1

    platforms = [Platform.SMARTSTORE, Platform.COUPANG, Platform.ZIGZAG, Platform.ABLY]

    while current <= end_dt:
        # current 는 해당 "시간 단위"의 시작 (분/초는 랜덤으로 분산)
        for platform in platforms:
            for _ in range(orders_per_hour_per_platform):
                minute_offset = random.randint(0, 59)
                order_dt = current + timedelta(minutes=minute_offset)
                seller_id = random.randint(MIN_SELLER_ID, MAX_SELLER_ID)
                _create_mock_order(db, platform, order_dt, global_seq, seller_id)
                global_seq += 1
                inserted += 1

        current += timedelta(hours=1)

    db.commit()
    return inserted


# ========================
# 2) 매 시간 신규 주문 삽입 배치
# ========================
def generate_hourly_new_orders(
    db: Session,
    target_hour: datetime | None = None,
    orders_per_platform: int = 3,
) -> int:
    """
    target_hour 기준 한 시간 구간에 대해, 각 플랫폼마다 orders_per_platform 개 생성
    - target_hour가 None이면 현재 시각의 "해당 시간"으로 처리
    - 각 주문은 seller_id (1~100) 중 랜덤 한 셀러에 귀속
    """
    if target_hour is None:
        now = datetime.now()
        target_hour = now.replace(minute=0, second=0, microsecond=0)

    start_dt = target_hour
    inserted = 0
    global_seq = int(target_hour.timestamp())  # 대충 유니크하게

    platforms = [Platform.SMARTSTORE, Platform.COUPANG, Platform.ZIGZAG, Platform.ABLY]

    for platform in platforms:
        for _ in range(orders_per_platform):
            minute_offset = random.randint(0, 59)
            order_dt = start_dt + timedelta(minutes=minute_offset)
            seller_id = random.randint(MIN_SELLER_ID, MAX_SELLER_ID)
            _create_mock_order(db, platform, order_dt, global_seq, seller_id)
            global_seq += 1
            inserted += 1

    db.commit()
    return inserted


# ========================
# 3) 매 시간 주문 상태 업데이트 배치
# ========================
def progress_order_statuses(
    db: Session,
    max_rows: int = 200,
) -> int:
    """
    아직 종단 상태(DELIVERED / CANCELLED)가 아닌 주문들 중 일부를
    다음 단계 상태로 진행시키는 배치
    """
    candidates: List[MockMarketOrder] = (
        db.query(MockMarketOrder)
        .filter(
            MockMarketOrder.status_normalized.in_(
                list(NORMALIZED_STATUS_FLOW.keys())
            )
        )
        .order_by(MockMarketOrder.order_datetime)
        .limit(max_rows)
        .all()
    )

    updated = 0

    for order in candidates:
        try:
            platform = Platform(order.platform)
        except ValueError:
            # 잘못된 platform 문자열이면 스킵
            continue

        current_norm = order.status_normalized or ""
        next_status = _next_status(platform, current_norm)
        if not next_status:
            continue

        next_raw, next_norm = next_status
        order.status_raw = next_raw
        order.status_normalized = next_norm

        # 결제 일시 없으면 채워주기
        if not order.pay_datetime and next_norm in (
            "PAID",
            "PREPARING_SHIPMENT",
            "SHIPPED",
            "DELIVERED",
        ):
            order.pay_datetime = order.order_datetime + timedelta(
                minutes=random.randint(0, 120)
            )

        # 배송 단계라면 택배사/송장 보정
        if next_norm in ("SHIPPED", "DELIVERED"):
            if not order.delivery_company or not order.delivery_company_code:
                company, code = _choose_delivery_company(platform)
                order.delivery_company = company
                order.delivery_company_code = code
            if not order.tracking_number:
                order.tracking_number = _generate_tracking_number(
                    platform,
                    order.order_datetime,
                    order.mock_order_item_id or 0,
                )

        # raw_payload는 여기서는 그대로 두고, 필요하면 나중에 regenerate 로직 추가
        updated += 1

    if updated:
        db.commit()

    return updated


# ========================
# 4) CLI로 한 번에 실행하고 싶을 때용
# ========================
if __name__ == "__main__":
    from argparse import ArgumentParser
    from .database import SessionLocal

    parser = ArgumentParser(description="Mock market orders generator")
    parser.add_argument(
        "--mode", choices=["initial", "hourly-insert", "hourly-update"], required=True
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.mode == "initial":
            count = generate_initial_mock_data(
                db,
                start_date=date(2025, 10, 1),
                end_date=date(2025, 11, 18),
                orders_per_hour_per_platform=3,
            )
            print(f"Inserted {count} mock orders (initial).")
        elif args.mode == "hourly-insert":
            count = generate_hourly_new_orders(db)
            print(f"Inserted {count} mock orders for the last hour.")
        elif args.mode == "hourly-update":
            updated = progress_order_statuses(db)
            print(f"Updated {updated} orders status.")
    finally:
        db.close()
