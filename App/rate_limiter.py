# App/rate_limiter.py

from __future__ import annotations

import time
from threading import Lock
from typing import Dict


class TokenBucket:
    """
    간단한 토큰 버킷 구현 (in-memory)
    - capacity: 최대 토큰 수 == 분당 허용 요청 수 (예: 60)
    - refill_rate_per_sec: 초당 채워지는 토큰 수 (예: 60/60 = 1)
    """

    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.tokens: float = float(capacity)
        self.refill_rate_per_sec = refill_rate_per_sec
        self.last_refill_ts: float = time.monotonic()
        self.lock = Lock()

    def allow(self, cost: float = 1.0) -> bool:
        """
        요청 1회당 cost 만큼 토큰을 소모.
        토큰이 충분하면 True, 아니면 False.
        """
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill_ts
            self.last_refill_ts = now

            # 경과시간만큼 토큰 채우기
            self.tokens += elapsed * self.refill_rate_per_sec
            if self.tokens > self.capacity:
                self.tokens = float(self.capacity)

            if self.tokens >= cost:
                self.tokens -= cost
                return True

            return False


# 전역 버킷 저장소 (API Key별)
_buckets: Dict[str, TokenBucket] = {}
_buckets_lock = Lock()


def check_rate_limit(api_key: str, limit_per_min: int) -> bool:
    """
    주어진 api_key에 대해 rate_limit_per_min 기준으로 토큰 버킷 체크.
    - 초당 refill_rate = limit_per_min / 60
    - True  => 허용
    - False => 차단 (429)
    """
    if limit_per_min <= 0:
        # 0 이하로 설정되어 있으면 무제한으로 간주
        return True

    refill_rate = float(limit_per_min) / 60.0

    with _buckets_lock:
        bucket = _buckets.get(api_key)

        # 없거나 capacity가 변경되었으면 새로 생성
        if bucket is None or bucket.capacity != limit_per_min:
            bucket = TokenBucket(capacity=limit_per_min, refill_rate_per_sec=refill_rate)
            _buckets[api_key] = bucket

    # 실제 토큰 소비
    return bucket.allow(cost=1.0)
