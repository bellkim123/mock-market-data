from typing import List

from .models import Order, Market


def to_smartstore_response(orders: List[Order]) -> dict:
    return {
        "orders": [
            {
                "orderNo": o.order_id,
                "orderDate": o.order_datetime.isoformat(),
                "buyerName": o.buyer_name,
                "items": [
                    {
                        "name": o.item_name,
                        "qty": o.qty,
                        "price": o.unit_price,
                    }
                ],
                "totalPrice": o.total_price,
            }
            for o in orders
        ]
    }


def to_coupang_response(orders: List[Order]) -> dict:
    return {
        "data": {
            "orderList": [
                {
                    "orderId": o.order_id,
                    "orderTimestamp": o.order_datetime.isoformat(),
                    "customerName": o.buyer_name,
                    "orderItems": [
                        {
                            "itemName": o.item_name,
                            "quantity": o.qty,
                            "unitPrice": o.unit_price,
                            "totalPrice": o.total_price,
                        }
                    ],
                }
                for o in orders
            ]
        }
    }


def to_elevenst_response(orders: List[Order]) -> dict:
    return {
        "result": "OK",
        "orders": [
            {
                "ordNo": o.order_id,
                "ordDttm": o.order_datetime.strftime("%Y%m%d%H%M%S"),
                "recvNm": o.buyer_name,
                "prdNm": o.item_name,
                "ordQty": o.qty,
                "payAmt": o.total_price,
            }
            for o in orders
        ],
    }


def to_ably_response(orders: List[Order]) -> dict:
    return {
        "success": True,
        "count": len(orders),
        "orders": [
            {
                "id": o.order_id,
                "ordered_at": o.order_datetime.isoformat(),
                "buyer": {
                    "name": o.buyer_name,
                },
                "line_items": [
                    {
                        "title": o.item_name,
                        "quantity": o.qty,
                        "price": o.unit_price,
                    }
                ],
                "amount": {
                    "total": o.total_price,
                },
            }
            for o in orders
        ],
    }


def to_market_response(market: Market, orders: List[Order]) -> dict:
    if market == Market.SMARTSTORE:
        return to_smartstore_response(orders)
    if market == Market.COUPANG:
        return to_coupang_response(orders)
    if market == Market.ELEVENST:
        return to_elevenst_response(orders)
    if market == Market.ABLY:
        return to_ably_response(orders)
    return {"orders": []}
