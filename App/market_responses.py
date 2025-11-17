# App/market_responses.py

from __future__ import annotations

from typing import List

from .models import MockMarketOrder, Platform


def _krw(amount: int | None) -> dict | None:
    """
    쿠팡 Money 타입 헬퍼
    amount가 None이면 None 리턴
    """
    if amount is None:
        return None

    return {
        "currencyCode": "KRW",
        "units": int(amount),
        "nanos": 0,
    }


# ========== SMARTSTORE MOCK ==========


def to_smartstore_response(orders: List[MockMarketOrder]) -> dict:
    """
    네이버 스마트스토어 스타일 간단 버전
    """
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "order": {
                    "orderId": o.external_order_id,
                    "orderDate": o.order_datetime.isoformat(),
                    "ordererId": o.buyer_id,
                    "ordererName": o.buyer_name,
                    "ordererTel": o.buyer_tel,
                    "orderDiscountAmount": o.discount_amount or 0,
                    "generalPaymentAmount": o.total_payment_amount or 0,
                },
                "productOrder": {
                    "productOrderId": o.external_order_item_id,
                    "productName": o.shop_name or "",
                    "quantity": o.quantity,
                    "totalPaymentAmount": o.total_payment_amount or 0,
                    "deliveryFeeAmount": o.shipping_fee or 0,
                    "productOrderStatus": o.status_raw,
                },
                "delivery": {
                    "deliveredDate": (o.pay_datetime or o.order_datetime).isoformat(),
                    "deliveryCompany": o.delivery_company,
                    "trackingNumber": o.tracking_number,
                },
            }
            for o in orders
        ],
    }


# ========== COUPANG MOCK ==========


def to_coupang_response(orders: List[MockMarketOrder]) -> dict:
    """
    질문에서 주신 쿠팡 발주서 조회 응답 구조에 맞춰 구성한 mock 응답
    (실제 스펙의 서브셋 + 기본값/더미값 섞어서 반환)
    """
    data: List[dict] = []

    for o in orders:
        # shipmentBoxId, orderId는 numeric이 아닐 수도 있으므로 안전하게 처리
        def _to_int_or_none(value: str | None):
            if value is None:
                return None
            v = value.strip()
            return int(v) if v.isdigit() else None

        shipment = {
            "shipmentBoxId": _to_int_or_none(o.external_order_id) or o.mock_order_item_id,
            "orderId": _to_int_or_none(o.external_order_id),
            "orderedAt": o.order_datetime.isoformat(),
            "orderer": {
                "name": o.buyer_name or "",
                "email": o.buyer_email or "",
                "safeNumber": o.buyer_tel or "",
                "ordererNumber": None,  # 별도 컬럼 없음
            },
            "paidAt": (o.pay_datetime or o.order_datetime).isoformat(),
            "status": o.status_normalized or o.status_raw,
            "shippingPrice": _krw(o.shipping_fee or 0),
            "remotePrice": None,
            "remoteArea": False,
            "parcelPrintMessage": o.memo or "",
            "splitShipping": False,
            "ableSplitShipping": False,
            "receiver": {
                "name": o.receiver_name or (o.buyer_name or ""),
                "safeNumber": o.receiver_tel or "",
                "receiverNumber": None,
                "addr1": o.receiver_address1 or "",
                "addr2": o.receiver_address2 or "",
                "postCode": o.receiver_zipcode or "",
            },
            "orderItems": [
                {
                    "vendorItemPackageId": 0,
                    "vendorItemPackageName": o.shop_name or "",
                    "productId": 0,  # 별도 productId 컬럼 없음
                    "vendorItemId": o.mock_order_item_id,
                    "vendorItemName": o.shop_name or "",
                    "shippingCount": o.quantity,
                    "salesPrice": _krw(o.product_amount or 0),
                    "orderPrice": _krw(o.total_payment_amount or 0),
                    "discountPrice": _krw(o.discount_amount or 0),
                    "instantCouponDiscount": _krw(0),
                    "downloadableCouponDiscount": _krw(0),
                    "coupangDiscount": _krw(0),
                    "externalVendorSkuCode": o.shop_id or "",
                    "etcInfoHeader": None,
                    "etcInfoValue": None,
                    "etcInfoValues": [],
                    "sellerProductId": 0,
                    "sellerProductName": o.shop_name or "",
                    "sellerProductItemName": o.shop_name or "",
                    "firstSellerProductItemName": o.shop_name or "",
                    "cancelCount": 0,
                    "holdCountForCancel": 0,
                    "estimatedShippingDate": o.order_datetime.date().isoformat(),
                    "plannedShippingDate": "",
                    "invoiceNumberUploadDate": "",
                    "extraProperties": {},
                    "pricingBadge": False,
                    "usedProduct": False,
                    "confirmDate": (o.pay_datetime or o.order_datetime).isoformat(),
                    "deliveryChargeTypeName": "유료"
                    if (o.shipping_fee or 0) > 0
                    else "무료",
                    "canceled": False,
                }
            ],
            "overseaShippingInfoDto": {
                "personalCustomsClearanceCode": "",
                "ordererSsn": "",
                "ordererPhoneNumber": "",
            },
            "deliveryCompanyName": o.delivery_company or "",
            "invoiceNumber": o.tracking_number or "",
            "inTrasitDateTime": o.order_datetime.isoformat(),
            "deliveredDate": (o.pay_datetime or o.order_datetime).isoformat(),
            "refer": "안드로이드앱",
            "shipmentType": "CGF LITE",
        }

        data.append(shipment)

    return {
        "code": 200,
        "message": "OK",
        "data": data,
        "nextToken": "",
    }


# ========== ZIGZAG MOCK ==========


def to_zigzag_response(orders: List[MockMarketOrder]) -> dict:
    """
    지그재그 스타일 간단 mock
    """
    return {
        "code": 200,
        "message": "success",
        "results": [
            {
                "order_item_number": o.external_order_item_id,
                "order": {
                    "order_number": o.external_order_id,
                    "orderer": {
                        "name": o.buyer_name,
                        "email": o.buyer_email,
                    },
                },
                "receiver": {
                    "name": o.receiver_name or o.buyer_name,
                },
                "date_created": int(o.order_datetime.timestamp() * 1000),
                "status": o.status_raw,
                "product_info": {
                    "name": o.shop_name or "",
                    "price": o.product_amount or 0,
                },
                "quantity": o.quantity,
                "total_amount": o.total_payment_amount or 0,
                "shop_name": o.shop_name,
                "payment_amount": {
                    "coupon_discount_amount": o.discount_amount or 0,
                },
            }
            for o in orders
        ],
    }


# ========== ABLY MOCK ==========


def to_ably_response(orders: List[MockMarketOrder]) -> dict:
    """
    에이블리 스타일 간단 mock
    """
    return {
        "code": 200,
        "message": "success",
        "result": [
            {
                "sno": o.external_order_item_id,
                "order_sno": o.external_order_id,
                "ea": o.quantity,
                "status": o.status_raw,
                "ordered_at": o.order_datetime.strftime("%Y-%m-%d %H:%M"),
                "buyer_name": o.buyer_name,
                "buyer_tel": o.buyer_tel,
                "buyer_email": o.buyer_email,
                "goods_name": o.shop_name or "",
                "pay_method_name": o.pay_method,
                "receiver_name": o.receiver_name,
                "receiver_tel": o.receiver_tel,
                "receiver_addr": (o.receiver_address1 or "")
                + " "
                + (o.receiver_address2 or ""),
                "receiver_postcode": o.receiver_zipcode,
                "price": o.product_amount or 0,
                "delivery_amount": o.shipping_fee or 0,
                "amount": o.total_payment_amount or 0,
            }
            for o in orders
        ],
    }


def to_platform_response(platform: Platform, orders: List[MockMarketOrder]) -> dict:
    if platform == Platform.SMARTSTORE:
        return to_smartstore_response(orders)
    if platform == Platform.COUPANG:
        return to_coupang_response(orders)
    if platform == Platform.ZIGZAG:
        return to_zigzag_response(orders)
    if platform == Platform.ABLY:
        return to_ably_response(orders)
    return {"code": 400, "message": "unsupported platform", "data": []}
