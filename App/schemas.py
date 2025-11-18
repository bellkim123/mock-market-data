# App/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field


# =========================================================
# 공통 에러 응답
# =========================================================

class ApiErrorResponse(BaseModel):
    code: int = Field(
        ...,
        description="응답 코드 (HTTP 코드와 별도로 API 내부에서 사용하는 코드)",
        example=400,
    )
    message: str = Field(
        ...,
        description="에러 메시지 (사용자/개발자 참고용)",
        example="page는 1 이상이어야 합니다.",
    )
    data: Optional[Any] = Field(
        None,
        description="에러 상세 정보 (문자열, 객체 등. 필요 시 확장)",
        example=None,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 400,
                "message": "page는 1 이상이어야 합니다.",
                "data": None,
            }
        }


# =========================================================
# SMARTSTORE 응답 스키마
# =========================================================

class SmartstoreOrder(BaseModel):
    orderId: str = Field(
        ...,
        description="스마트스토어 주문번호 (예: 2025111823-470081)",
        example="2025111823-470081",
    )
    orderDate: datetime = Field(
        ...,
        description="주문 일시 (ISO8601 포맷)",
        example="2025-11-18T23:11:00",
    )
    ordererId: str = Field(
        ...,
        description="주문자 ID (로그인 ID 등)",
        example="user_5296",
    )
    ordererName: str = Field(
        ...,
        description="주문자 이름",
        example="정유진",
    )
    ordererTel: str = Field(
        ...,
        description="주문자 전화번호",
        example="010-8081-1279",
    )
    orderDiscountAmount: int = Field(
        ...,
        description="주문 단위 전체 할인 금액 합계 (쿠폰/즉시할인 등)",
        example=0,
    )
    generalPaymentAmount: int = Field(
        ...,
        description="주문 단위 실 결제 금액 합계 (100원 단위)",
        example=61400,
    )


class SmartstoreProductOrder(BaseModel):
    productOrderId: str = Field(
        ...,
        description="스마트스토어 주문상품번호",
        example="2025111823-470081-P470081",
    )
    productName: str = Field(
        ...,
        description="상품명",
        example="데일리룩",
    )
    quantity: int = Field(
        ...,
        description="주문 수량",
        example=2,
    )
    totalPaymentAmount: int = Field(
        ...,
        description="해당 주문상품 결제 금액 (100원 단위)",
        example=61400,
    )
    deliveryFeeAmount: int = Field(
        ...,
        description="해당 주문상품에 배분된 배송비 금액",
        example=3000,
    )
    productOrderStatus: str = Field(
        ...,
        description=(
            "상품 상태 원본값\n"
            "- 공통 정규화 상태: PAID / PREPARING_SHIPMENT / SHIPPED / DELIVERED / CANCELLED\n"
            "- Smartstore 원본 상태값 목록:\n"
            "  - 결제완료 (PAID)\n"
            "  - 상품준비중 (PREPARING_SHIPMENT)\n"
            "  - 배송중 (SHIPPED)\n"
            "  - 배송완료, 구매확정 (DELIVERED)\n"
            "  - 주문취소, 결제취소 (CANCELLED)"
        ),
        example="배송중",
    )


class SmartstoreDelivery(BaseModel):
    deliveredDate: datetime = Field(
        ...,
        description="배송 완료(또는 결제 완료) 일시",
        example="2025-11-18T23:34:00",
    )
    deliveryCompany: str = Field(
        ...,
        description=(
            "택배사 이름\n"
            "- 사용 가능한 값:\n"
            "  - CJ대한통운 (코드: CJGLS)\n"
            "  - 롯데택배 (코드: LOTTES)\n"
            "  - 한진택배 (코드: HANJIN)"
        ),
        example="CJ대한통운",
    )
    trackingNumber: str = Field(
        ...,
        description="운송장 번호",
        example="CJ11188190076",
    )


class SmartstoreOrderBlock(BaseModel):
    order: SmartstoreOrder = Field(..., description="주문 단위 정보")
    productOrder: SmartstoreProductOrder = Field(
        ..., description="상품 단위 정보"
    )
    delivery: SmartstoreDelivery = Field(
        ..., description="배송/택배 정보"
    )


class SmartstoreOrdersResponse(BaseModel):
    code: int = Field(
        ...,
        description="응답 코드 (200: 성공)",
        example=200,
    )
    message: str = Field(
        ...,
        description="응답 메시지 (예: success)",
        example="success",
    )
    data: List[SmartstoreOrderBlock] = Field(
        ...,
        description="주문 리스트",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": [
                    {
                        "order": {
                            "orderId": "2025111823-470081",
                            "orderDate": "2025-11-18T23:11:00",
                            "ordererId": "user_5296",
                            "ordererName": "정유진",
                            "ordererTel": "010-8081-1279",
                            "orderDiscountAmount": 0,
                            "generalPaymentAmount": 61400,
                        },
                        "productOrder": {
                            "productOrderId": "2025111823-470081-P470081",
                            "productName": "데일리룩",
                            "quantity": 2,
                            "totalPaymentAmount": 61400,
                            "deliveryFeeAmount": 3000,
                            "productOrderStatus": "배송중",
                        },
                        "delivery": {
                            "deliveredDate": "2025-11-18T23:34:00",
                            "deliveryCompany": "CJ대한통운",
                            "trackingNumber": "CJ11188190076",
                        },
                    }
                ],
            }
        }


# =========================================================
# COUPANG 응답 스키마
# =========================================================

class CoupangMoney(BaseModel):
    currencyCode: str = Field(
        ...,
        description="통화 코드 (항상 KRW)",
        example="KRW",
    )
    units: int = Field(
        ...,
        description="정수 금액 (100원 단위)",
        example=23800,
    )
    nanos: int = Field(
        ...,
        description="소수 금액 (현재는 항상 0)",
        example=0,
    )


class CoupangOrderer(BaseModel):
    name: str = Field(
        ...,
        description="주문자 이름",
        example="김철수",
    )
    email: str = Field(
        ...,
        description="주문자 이메일",
        example="mock9020@example.com",
    )
    safeNumber: str = Field(
        ...,
        description="안심번호",
        example="010-3061-6823",
    )
    ordererNumber: str = Field(
        ...,
        description="주문자 일반 전화번호 (없을 수 있음)",
        example="",
    )


class CoupangReceiver(BaseModel):
    name: str = Field(
        ...,
        description="수령인 이름",
        example="배송수령인",
    )
    safeNumber: str = Field(
        ...,
        description="수령인 안심번호",
        example="010-4702-3473",
    )
    receiverNumber: str = Field(
        ...,
        description="수령인 일반 전화번호 (없을 수 있음)",
        example="",
    )
    addr1: str = Field(
        ...,
        description="주소 1 (도로명/지번 등)",
        example="서울특별시 테스트구 테스트로 123",
    )
    addr2: str = Field(
        ...,
        description="주소 2 (상세주소)",
        example="테스트아파트 101동 1001호",
    )
    postCode: str = Field(
        ...,
        description="우편번호",
        example="87455",
    )


class CoupangOrderItem(BaseModel):
    vendorItemPackageId: int = Field(
        ...,
        description="쿠팡 Vendor Item 패키지 ID (없으면 0)",
        example=0,
    )
    vendorItemPackageName: str = Field(
        ...,
        description="Vendor Item 패키지명",
        example="팔랑샵",
    )
    productId: int = Field(
        ...,
        description="쿠팡 상품 ID (모의 데이터에서는 0 사용)",
        example=0,
    )
    vendorItemId: int = Field(
        ...,
        description="Vendor Item ID",
        example=9339,
    )
    vendorItemName: str = Field(
        ...,
        description="Vendor Item 이름",
        example="팔랑샵",
    )
    shippingCount: int = Field(
        ...,
        description="배송 수량 (박스 수 등)",
        example=3,
    )
    salesPrice: CoupangMoney = Field(
        ...,
        description="상품 1개당 판매가",
    )
    orderPrice: CoupangMoney = Field(
        ...,
        description="해당 상품 전체 주문 금액 (수량 * 판매가)",
    )
    discountPrice: CoupangMoney = Field(
        ...,
        description="즉시할인/쿠폰 등 할인 금액",
    )
    instantCouponDiscount: CoupangMoney = Field(
        ...,
        description="즉시 쿠폰 할인 금액",
    )
    downloadableCouponDiscount: CoupangMoney = Field(
        ...,
        description="다운로드 쿠폰 할인 금액",
    )
    coupangDiscount: CoupangMoney = Field(
        ...,
        description="쿠팡 자체 할인 금액",
    )
    externalVendorSkuCode: str = Field(
        ...,
        description="외부 시스템에서 사용하는 SKU 코드",
        example="SHOP-CO-023",
    )
    etcInfoHeader: str = Field(
        ...,
        description="기타 옵션 헤더",
        example="",
    )
    etcInfoValue: str = Field(
        ...,
        description="기타 옵션 값",
        example="",
    )
    etcInfoValues: List[str] = Field(
        ...,
        description="기타 옵션 값 리스트",
        example=[],
    )
    sellerProductId: int = Field(
        ...,
        description="셀러 상품 ID (없으면 0)",
        example=0,
    )
    sellerProductName: str = Field(
        ...,
        description="셀러 상품명",
        example="팔랑샵",
    )
    sellerProductItemName: str = Field(
        ...,
        description="셀러 상품 아이템명",
        example="팔랑샵",
    )
    firstSellerProductItemName: str = Field(
        ...,
        description="첫 번째 셀러 상품 아이템명",
        example="팔랑샵",
    )
    cancelCount: int = Field(
        ...,
        description="취소 수량",
        example=0,
    )
    holdCountForCancel: int = Field(
        ...,
        description="취소 대기 수량",
        example=0,
    )
    estimatedShippingDate: str = Field(
        ...,
        description="예상 발송 일자 (YYYY-MM-DD)",
        example="2025-10-01",
    )
    plannedShippingDate: str = Field(
        ...,
        description="계획 발송 일자 (없는 경우 빈 문자열)",
        example="",
    )
    invoiceNumberUploadDate: str = Field(
        ...,
        description="송장번호 업로드 일시",
        example="",
    )
    extraProperties: dict = Field(
        ...,
        description="기타 속성 키-값",
        example={},
    )
    pricingBadge: bool = Field(
        ...,
        description="특가/뱃지 여부",
        example=False,
    )
    usedProduct: bool = Field(
        ...,
        description="중고상품 여부",
        example=False,
    )
    confirmDate: str = Field(
        ...,
        description="구매 확정 일시 (YYYY-MM-DDThh:mm:ss)",
        example="2025-10-02T00:32:00",
    )
    deliveryChargeTypeName: str = Field(
        ...,
        description="배송비 유형명 (예: 무료, 조건부무료 등)",
        example="무료",
    )
    canceled: bool = Field(
        ...,
        description="해당 상품이 취소되었는지 여부",
        example=False,
    )


class CoupangOverseaInfo(BaseModel):
    personalCustomsClearanceCode: str = Field(
        ...,
        description="개인 통관 고유부호",
        example="",
    )
    ordererSsn: str = Field(
        ...,
        description="주문자 주민등록번호 (사용하지 않음)",
        example="",
    )
    ordererPhoneNumber: str = Field(
        ...,
        description="주문자 전화번호 (해외배송용)",
        example="",
    )


class CoupangShipment(BaseModel):
    shipmentBoxId: int = Field(
        ...,
        description="쿠팡 배송박스 ID",
        example=220251001239327,
    )
    orderId: Optional[int] = Field(
        ...,
        description="쿠팡 주문 ID",
        example=220251001239327,
    )
    orderedAt: str = Field(
        ...,
        description="주문 일시 (쿠팡 포맷, ISO8601)",
        example="2025-10-01T23:46:00",
    )
    orderer: CoupangOrderer = Field(
        ...,
        description="주문자 정보",
    )
    paidAt: str = Field(
        ...,
        description="결제 완료 일시",
        example="2025-10-02T00:32:00",
    )
    status: str = Field(
        ...,
        description=(
            "쿠팡 배송/주문 상태 (원본값)\n"
            "- 공통 정규화 상태: PAID / PREPARING_SHIPMENT / SHIPPED / DELIVERED / CANCELLED\n"
            "- Coupang 원본 상태값 목록:\n"
            "  - ACCEPT (PAID)\n"
            "  - INSTRUCT (PREPARING_SHIPMENT)\n"
            "  - IN_DELIVERY (SHIPPED)\n"
            "  - FINAL_DELIVERY (DELIVERED)\n"
            "  - CANCELED (CANCELLED)"
        ),
        example="ACCEPT",
    )
    shippingPrice: CoupangMoney = Field(
        ...,
        description="배송비 금액",
    )
    remotePrice: CoupangMoney = Field(
        ...,
        description="도서/산간 추가 배송비 금액",
    )
    remoteArea: bool = Field(
        ...,
        description="도서산간 지역 여부",
        example=False,
    )
    parcelPrintMessage: str = Field(
        ...,
        description="송장 출력 메모",
        example="빠른 배송 부탁드려요.",
    )
    splitShipping: bool = Field(
        ...,
        description="분할배송 여부",
        example=False,
    )
    ableSplitShipping: bool = Field(
        ...,
        description="분할배송 가능 여부",
        example=False,
    )
    receiver: CoupangReceiver = Field(
        ...,
        description="수령인 정보",
    )
    orderItems: List[CoupangOrderItem] = Field(
        ...,
        description="주문 상품 리스트",
    )
    overseaShippingInfoDto: CoupangOverseaInfo = Field(
        ...,
        description="해외 배송 추가 정보",
    )
    deliveryCompanyName: str = Field(
        ...,
        description=(
            "배송사 이름\n"
            "- 사용 가능한 값:\n"
            "  - 쿠팡로지스틱스 (코드: CPLG)\n"
            "  - CJ대한통운 (코드: CJP)\n"
            "※ 아직 출고 전이면 빈 문자열"
        ),
        example="",
    )
    invoiceNumber: str = Field(
        ...,
        description="운송장 번호 (출고 전이면 빈 문자열)",
        example="",
    )
    inTrasitDateTime: str = Field(
        ...,
        description="배송 시작(집하) 일시",
        example="2025-10-01T23:46:00",
    )
    deliveredDate: str = Field(
        ...,
        description="배송 완료 일시",
        example="2025-10-02T00:32:00",
    )
    refer: str = Field(
        ...,
        description="주문 채널 정보 (예: 안드로이드앱, 아이폰앱 등)",
        example="안드로이드앱",
    )
    shipmentType: str = Field(
        ...,
        description="배송 타입 (예: CGF LITE)",
        example="CGF LITE",
    )


class CoupangOrdersResponse(BaseModel):
    code: int = Field(
        ...,
        description="응답 코드 (200: 성공)",
        example=200,
    )
    message: str = Field(
        ...,
        description="응답 메시지 (예: OK)",
        example="OK",
    )
    data: List[CoupangShipment] = Field(
        ...,
        description="배송박스(주문) 리스트",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "OK",
                "data": [
                    {
                        "shipmentBoxId": 220251001239327,
                        "orderId": 220251001239327,
                        "orderedAt": "2025-10-01T23:46:00",
                        "orderer": {
                            "name": "김철수",
                            "email": "mock9020@example.com",
                            "safeNumber": "010-3061-6823",
                            "ordererNumber": "",
                        },
                        "paidAt": "2025-10-02T00:32:00",
                        "status": "ACCEPT",
                        "shippingPrice": {
                            "currencyCode": "KRW",
                            "units": 0,
                            "nanos": 0,
                        },
                        "remotePrice": {
                            "currencyCode": "KRW",
                            "units": 0,
                            "nanos": 0,
                        },
                        "remoteArea": False,
                        "parcelPrintMessage": "빠른 배송 부탁드려요.",
                        "splitShipping": False,
                        "ableSplitShipping": False,
                        "receiver": {
                            "name": "배송수령인",
                            "safeNumber": "010-4702-3473",
                            "receiverNumber": "",
                            "addr1": "서울특별시 테스트구 테스트로 123",
                            "addr2": "테스트아파트 101동 1001호",
                            "postCode": "87455",
                        },
                        "orderItems": [
                            {
                                "vendorItemPackageId": 0,
                                "vendorItemPackageName": "팔랑샵",
                                "productId": 0,
                                "vendorItemId": 9339,
                                "vendorItemName": "팔랑샵",
                                "shippingCount": 3,
                                "salesPrice": {
                                    "currencyCode": "KRW",
                                    "units": 7900,
                                    "nanos": 0,
                                },
                                "orderPrice": {
                                    "currencyCode": "KRW",
                                    "units": 23800,
                                    "nanos": 0,
                                },
                                "discountPrice": {
                                    "currencyCode": "KRW",
                                    "units": 0,
                                    "nanos": 0,
                                },
                                "instantCouponDiscount": {
                                    "currencyCode": "KRW",
                                    "units": 0,
                                    "nanos": 0,
                                },
                                "downloadableCouponDiscount": {
                                    "currencyCode": "KRW",
                                    "units": 0,
                                    "nanos": 0,
                                },
                                "coupangDiscount": {
                                    "currencyCode": "KRW",
                                    "units": 0,
                                    "nanos": 0,
                                },
                                "externalVendorSkuCode": "SHOP-CO-023",
                                "etcInfoHeader": "",
                                "etcInfoValue": "",
                                "etcInfoValues": [],
                                "sellerProductId": 0,
                                "sellerProductName": "팔랑샵",
                                "sellerProductItemName": "팔랑샵",
                                "firstSellerProductItemName": "팔랑샵",
                                "cancelCount": 0,
                                "holdCountForCancel": 0,
                                "estimatedShippingDate": "2025-10-01",
                                "plannedShippingDate": "",
                                "invoiceNumberUploadDate": "",
                                "extraProperties": {},
                                "pricingBadge": False,
                                "usedProduct": False,
                                "confirmDate": "2025-10-02T00:32:00",
                                "deliveryChargeTypeName": "무료",
                                "canceled": False,
                            }
                        ],
                        "overseaShippingInfoDto": {
                            "personalCustomsClearanceCode": "",
                            "ordererSsn": "",
                            "ordererPhoneNumber": "",
                        },
                        "deliveryCompanyName": "",
                        "invoiceNumber": "",
                        "inTrasitDateTime": "2025-10-01T23:46:00",
                        "deliveredDate": "2025-10-02T00:32:00",
                        "refer": "안드로이드앱",
                        "shipmentType": "CGF LITE",
                    }
                ],
            }
        }


# =========================================================
# ZIGZAG 응답 스키마
# =========================================================

class ZigzagOrderer(BaseModel):
    name: str = Field(
        ...,
        description="주문자 이름",
        example="정유진",
    )
    email: str = Field(
        ...,
        description="주문자 이메일",
        example="mock6008@example.com",
    )


class ZigzagOrder(BaseModel):
    order_number: str = Field(
        ...,
        description="지그재그 주문 번호",
        example="ZZ20251119001763478006",
    )
    orderer: ZigzagOrderer = Field(
        ...,
        description="주문자 정보",
    )


class ZigzagReceiver(BaseModel):
    name: str = Field(
        ...,
        description="수령인 이름",
        example="정유진",
    )


class ZigzagProductInfo(BaseModel):
    name: str = Field(
        ...,
        description="상품명",
        example="팔랑샵",
    )
    price: int = Field(
        ...,
        description="상품 단가 (100원 단위)",
        example=30000,
    )


class ZigzagPaymentAmount(BaseModel):
    coupon_discount_amount: int = Field(
        ...,
        description="쿠폰 할인 금액",
        example=0,
    )


class ZigzagResultItem(BaseModel):
    order_item_number: str = Field(
        ...,
        description="지그재그 주문 상품 번호",
        example="ZZIT20251119001763478006",
    )
    order: ZigzagOrder = Field(
        ...,
        description="주문 단위 정보",
    )
    receiver: ZigzagReceiver = Field(
        ...,
        description="수령인 정보",
    )
    date_created: int = Field(
        ...,
        description="주문 생성 시간 (epoch millis)",
        example=1763479980000,
    )
    status: str = Field(
        ...,
        description=(
            "지그재그 주문/배송 상태 (원본값)\n"
            "- 공통 정규화 상태: PAID / PREPARING_SHIPMENT / SHIPPED / DELIVERED / CANCELLED\n"
            "- Zigzag 원본 상태값 목록:\n"
            "  - PAY_COMPLETE (PAID)\n"
            "  - DELIVERY_READY (PREPARING_SHIPMENT)\n"
            "  - DELIVERY_IN_PROGRESS (SHIPPED)\n"
            "  - DELIVERY_COMPLETED (DELIVERED)\n"
            "  - ORDER_CANCEL (CANCELLED)"
        ),
        example="DELIVERY_COMPLETED",
    )
    product_info: ZigzagProductInfo = Field(
        ...,
        description="상품 정보",
    )
    quantity: int = Field(
        ...,
        description="주문 수량",
        example=3,
    )
    total_amount: int = Field(
        ...,
        description="총 결제 금액 (100원 단위)",
        example=90000,
    )
    shop_name: str = Field(
        ...,
        description="샵 이름",
        example="팔랑샵",
    )
    payment_amount: ZigzagPaymentAmount = Field(
        ...,
        description="결제 금액 상세 정보",
    )


class ZigzagOrdersResponse(BaseModel):
    code: int = Field(
        ...,
        description="응답 코드 (200: 성공)",
        example=200,
    )
    message: str = Field(
        ...,
        description="응답 메시지",
        example="success",
    )
    results: List[ZigzagResultItem] = Field(
        ...,
        description="주문 상품 리스트",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "results": [
                    {
                        "order_item_number": "ZZIT20251119001763478006",
                        "order": {
                            "order_number": "ZZ20251119001763478006",
                            "orderer": {
                                "name": "정유진",
                                "email": "mock6008@example.com",
                            },
                        },
                        "receiver": {"name": "정유진"},
                        "date_created": 1763479980000,
                        "status": "DELIVERY_COMPLETED",
                        "product_info": {
                            "name": "팔랑샵",
                            "price": 30000,
                        },
                        "quantity": 3,
                        "total_amount": 90000,
                        "shop_name": "팔랑샵",
                        "payment_amount": {
                            "coupon_discount_amount": 0,
                        },
                    }
                ],
            }
        }


# =========================================================
# ABLY 응답 스키마
# =========================================================

class AblyOrderItem(BaseModel):
    sno: str = Field(
        ...,
        description="에이블리 주문 상품 고유 번호",
        example="1763478009",
    )
    order_sno: str = Field(
        ...,
        description="에이블리 주문 번호",
        example="AB20251119001763478009",
    )
    ea: int = Field(
        ...,
        description="주문 수량",
        example=3,
    )
    status: str = Field(
        ...,
        description=(
            "에이블리 주문 상태 (원본값)\n"
            "- 공통 정규화 상태: PAID / PREPARING_SHIPMENT / SHIPPED / DELIVERED / CANCELLED\n"
            "- Ably 원본 상태값 목록:\n"
            "  - 결제완료 (PAID)\n"
            "  - 배송준비중 (PREPARING_SHIPMENT)\n"
            "  - 배송중 (SHIPPED)\n"
            "  - 배송완료 (DELIVERED)\n"
            "  - 취소완료 (CANCELLED)"
        ),
        example="배송완료",
    )
    ordered_at: str = Field(
        ...,
        description="주문 일시 (YYYY-MM-DD HH:mm)",
        example="2025-11-19 00:54",
    )
    buyer_name: str = Field(
        ...,
        description="구매자 이름",
        example="김철수",
    )
    buyer_tel: str = Field(
        ...,
        description="구매자 전화번호",
        example="010-1359-5757",
    )
    buyer_email: str = Field(
        ...,
        description="구매자 이메일",
        example="mock7044@example.com",
    )
    goods_name: str = Field(
        ...,
        description="상품명",
        example="위시어스",
    )
    pay_method_name: str = Field(
        ...,
        description="결제 수단명 (CARD, KAKAO_PAY, NAVER_PAY, TOSS_PAY, 무통장입금 등)",
        example="KAKAO_PAY",
    )
    receiver_name: str = Field(
        ...,
        description="수령인 이름",
        example="김철수",
    )
    receiver_tel: str = Field(
        ...,
        description="수령인 전화번호",
        example="010-4148-6736",
    )
    receiver_addr: str = Field(
        ...,
        description="수령 주소 (도로명 + 상세 포함)",
        example="서울특별시 테스트구 테스트로 123 테스트아파트 101동 1001호",
    )
    receiver_postcode: str = Field(
        ...,
        description="우편번호",
        example="68958",
    )
    price: int = Field(
        ...,
        description="상품 단가 (100원 단위)",
        example=30000,
    )
    delivery_amount: int = Field(
        ...,
        description=(
            "배송비 금액 (100원 단위)\n"
            "- Ably 배송사/코드 목록 (generator 기준):\n"
            "  - 우체국택배 (코드: KOREAPOST_AB)\n"
            "  - CJ대한통운 (코드: CJ_AB)"
        ),
        example=0,
    )
    amount: int = Field(
        ...,
        description="총 결제 금액 (상품가 * 수량 + 배송비 - 할인, 100원 단위)",
        example=90000,
    )


class AblyOrdersResponse(BaseModel):
    code: int = Field(
        ...,
        description="응답 코드 (200: 성공)",
        example=200,
    )
    message: str = Field(
        ...,
        description="응답 메시지",
        example="success",
    )
    result: List[AblyOrderItem] = Field(
        ...,
        description="주문 상품 리스트",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "result": [
                    {
                        "sno": "1763478009",
                        "order_sno": "AB20251119001763478009",
                        "ea": 3,
                        "status": "배송완료",
                        "ordered_at": "2025-11-19 00:54",
                        "buyer_name": "김철수",
                        "buyer_tel": "010-1359-5757",
                        "buyer_email": "mock7044@example.com",
                        "goods_name": "위시어스",
                        "pay_method_name": "KAKAO_PAY",
                        "receiver_name": "김철수",
                        "receiver_tel": "010-4148-6736",
                        "receiver_addr": "서울특별시 테스트구 테스트로 123 테스트아파트 101동 1001호",
                        "receiver_postcode": "68958",
                        "price": 30000,
                        "delivery_amount": 0,
                        "amount": 90000,
                    }
                ],
            }
        }