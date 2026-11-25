"""Giới hạn tốc độ theo IP (cửa sổ trượt, trong bộ nhớ tiến trình).

Phù hợp một tiến trình (modular monolith, không Redis). Không tin header X-Forwarded-For.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from common.errors import ProblemError


class SlidingWindowLimiter:
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int) -> int:
        """Ghi một lượt; trả 0 nếu cho phép, ngược lại số giây phải chờ."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= limit:
                return max(1, int(self.window - (now - q[0])) + 1)
            q.append(now)
            return 0


def rate_limited(scope: str):
    """Dependency FastAPI: giới hạn `rate_limit_per_minute` request mỗi IP cho mỗi scope (0 = tắt)."""

    def dependency(request: Request) -> None:
        limit = request.app.state.settings.rate_limit_per_minute
        if limit <= 0:
            return
        ip = request.client.host if request.client else "unknown"
        wait = request.app.state.limiter.hit(f"{scope}:{ip}", limit)
        if wait:
            raise ProblemError(
                429, "rate-limited", "Bạn thao tác quá nhanh. Vui lòng thử lại sau ít phút.",
                headers={"Retry-After": str(wait)},
            )

    return dependency
