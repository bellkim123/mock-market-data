**모의 마켓 주문 API**입니다.  
실제 Smartstore / Coupang / Zigzag / Ably API 구조를 참고했습니다.

---
## 1. 기본 정보

- 인증 방식: **API Key (X-API-Key 헤더)**

### 1.1 인증 헤더

| 항목      | 값 예시                | 설명                                        |
|----------|------------------------|---------------------------------------------|
| X-API-Key | `SELLER001-COUP-9F3A2` | 필수. `mock_api_clients.api_key` 와 매핑됨 |

`mock_api_clients` 테이블 구조:

- `seller_id` (1~100)
- `seller_name`
- `platform` : `SMARTSTORE` / `COUPANG` / `ZIGZAG` / `ABLY`
- `rate_limit_per_min` : 분당 허용 요청 수
- `is_active` : 0/1 (비활성/활성)
---
## 2. 공통 Query 파라미터

모든 주문 조회 API에 공통으로 적용됩니다.

| 이름         | 타입 | 필수 | 기본값 | 제약      | 설명                                                       |
|--------------|------|------|--------|-----------|------------------------------------------------------------|
| `page`       | int  | N    | 1      | `>= 1`    | 페이지 번호 (1부터 시작)                                   |
| `page_size`  | int  | N    | 50     | `1~100`   | 페이지당 주문 건수. 100 초과 시 400 에러                    |
| `start_date` | date | N    | 없음   | -         | 조회 시작일 (`YYYY-MM-DD`). `order_datetime >= start`     |
| `end_date`   | date | N    | 없음   | -         | 조회 종료일 (`YYYY-MM-DD`). `order_datetime <= end`       |

> **페이징 규칙**
> - `page`, `page_size` 둘 다 쿼리스트링으로 전달
> - 빈 배열이 반환되면 더 이상 다음 페이지가 없는 것으로 간주

---

## 3. 엔드포인트

### 3.1 Smartstore 주문 조회

- **Method**: `GET`
- **Path**: `/smartstore/orders`
- **Auth**: `X-API-Key` (platform=`SMARTSTORE` 인 키만 허용)

#### 요청 예시

```bash
curl -X GET \
  "http://127.0.0.1:8000/smartstore/orders?page=1&page_size=50&start_date=2025-10-01&end_date=2025-10-31" \
  -H "X-API-Key: SELLER001-SS-ABCDE"
