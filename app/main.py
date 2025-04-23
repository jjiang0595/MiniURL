import base64
import validators
import os
import redis
import hashlib
import datetime
from http.client import HTTPException
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request, Body
from app.rate_limiter import RateLimiter
from starlette.responses import RedirectResponse
from fastapi.responses import JSONResponse

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
limiter = RateLimiter()

load_dotenv()
BASE_URL = os.getenv('BASE_URL')
RATE_LIMIT, RATE_WINDOW = os.getenv('RATE_LIMIT') if not os.getenv('LOAD_TEST') else 100000, os.getenv('RATE_WINDOW')
base_url = os.getenv(f'{BASE_URL}', "http://127.0.0.1:8000/")


@app.middleware("http")
async def middleware(request: Request, call_next):
    """
    Applies rate limits to all requests if rate limit is reached.
    Bypass rate limits if there is a connection error with Redis.

    Returns: 429 or proxied response
    """
    try:
         allowed, remaining = limiter.is_rate_limited(request, limit=int(RATE_LIMIT), window=int(RATE_WINDOW))
    except ConnectionError:
         response = await call_next(request)
         response.headers["X-RateLimit-Bypass"] = "Redis Failure"
         return response

    if not allowed:
         return JSONResponse(
              content={"error": "Rate limit exceeded"},
              status_code=429,
              headers={"X-RateLimit-Reset": str(RATE_WINDOW)}
         )
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


def get_redis():
     return r


def hash_url(url: str):
     """  Generates a URL hash using SHA-256 and Base64 encoding
          Uses:
          - HA-256: Minimizes collision risk
          - Base64 URL-safe encoding: Creates a 6-character URL-friendly string

          Returns:
          str: 6-character Base64-encoded hash of the URL
     """
     digest = hashlib.sha256(url.encode()).digest()
     b64 = base64.urlsafe_b64encode(digest).decode()
     return b64[:6].strip("=")


@app.get("/api/urls/{url_code}")
def get_url_metadata(url_code: str):
     """  Retrieves URL metadata

          Returns:
          str: original url
          int: amount of visits to the URL
          str: expiry time of the URL in HH:MM:SS format
     """
     if not r.exists(f"{url_code}:url"):
          raise HTTPException(status_code=404, detail="URL code not found")
     clicks = r.get(f"{url_code}:clicks") or 0
     return {
          "original_url": r.get(f"{url_code}:url"),
          "clicks": int(clicks),
          "expiry_time": str(datetime.timedelta(seconds=r.ttl(f"{url_code}:url"))),
          }


@app.post("/shorten")
def shorten_url(url: str = Body(..., embed=True)):
     """
     Shortens a URL with a 24-hour expiry

     Returns: type[str, str, str]
     str: Original URL
     str: Shortened URL
     str: URL hash
     """

     if not validators.url(url):
          raise HTTPException(status_code=400, detail="Invalid URL")
     url_code = hash_url(url)

     r.set(f"{url_code}:url", url, nx=True, ex=60 * 60 * 24)

     return {
          "original_url": url,
          "short_url": base_url + url_code,
          "short_code": url_code,
     }

@app.get("/{url_code}")
def redirect(url_code: str, r: redis.Redis = Depends(get_redis)):
     """
     Redirects to the original URL and increments URL click count

     Returns: 307 (Successful Redirect)
     Raises: 404 (URL not found)
     """
     if not r.get(f"{url_code}:url"):
          raise HTTPException(status_code=404,detail="URL not found")

     r.incr(f"{url_code}:clicks")
     return RedirectResponse(r.get(f"{url_code}:url"))