"""
Rate Limiter 유틸리티
"""
import time

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def acquire(self):
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.calls = [t for t in self.calls if now - t < self.period]
        self.calls.append(time.time())

# 전역 Rate Limiter 인스턴스
rate_limiter = RateLimiter(8, 1)  # Upbit 초당 10회 제한, 여유 있게 8회
