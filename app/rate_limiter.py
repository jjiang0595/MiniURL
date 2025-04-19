import redis
from fastapi import Request

class RateLimiter:
    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port)

    def get_user_ip(self, request: Request):
        """ Extracts client IP using X-Forwarded-For (proxies) or direct connection """
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        return request.client.host or "127.0.0.1"

    def is_rate_limited(self, request: Request, limit: int, window: int):
        """
        Enforces rate limits using Redis pipelining for atomic increments and expiry.

        Use a sliding window algorithm to:
        - Atomically increment request count and set expiration time on first request

        Returns: tuple[bool, int]
        bool: is_rate_limited
        int: remaining requests
        """
        ip = self.get_user_ip(request)
        key = f"rate_limit:{ip}"

        pipeline = self.redis.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, window, nx=True)
        request_count, _ = pipeline.execute()

        remaining = max(0, limit - request_count)
        return request_count <= limit, remaining

