import pytest
from fakeredis import FakeRedis
from fastapi import HTTPException, status
from app.main import hash_url, shorten_url, get_url_metadata, redirect, app, get_redis
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def fake_redis():
    """ Initialize FakeRedis with teardown """
    r = FakeRedis()
    yield r
    r.flushall()


@pytest.fixture
def client(fake_redis: FakeRedis):
    """ Initialize FastAPI TestClient with Redis override """
    app.dependency_overrides[get_redis] = lambda: fake_redis
    yield TestClient(app)
    app.dependency_overrides = {}


def test_middleware_allows_requests(client: TestClient):
    """ Test:
        - Requests under rate limit are allowed
        - Correct X-RateLimit headers
        - Returns 200 status code
    """
    with patch("app.main.limiter.is_rate_limited", return_value=(True, 95)):
        response = client.get("/docs")
        assert "X-RateLimit-Remaining" in response.headers
        assert response.status_code == 200


def test_middleware_blocks_requests(client: TestClient):
    """ Test:
            - Requests over rate limit are not allowed
            - Returns 429 status code
        """
    with patch("app.main.limiter.is_rate_limited", return_value=(False, 0)):
        response = client.get("/")
        assert response.status_code == 429


def test_middleware_redis_failure(client: TestClient):
    """ Test:
            - Failed Redis connections don't block requests
            - Correct X-RateLimit headers
            - Returns 200 status code (fail-open)
        """
    with patch("app.main.limiter.is_rate_limited", side_effect=ConnectionError):
        response = client.get("/docs")
        assert "X-RateLimit-Bypass"in response.headers
        assert response.status_code == 200


def test_hash_url():
    """ Test hash validity & uniqueness """
    url = "https://google.com"

    assert len(hash_url(url)) == 6
    assert hash_url(url) == hash_url(url)
    assert hash_url(url) != hash_url(url + "a")


def test_shorten_url(client: TestClient):
    """ Test:
            - URLs are properly stored to Redis with correct key/expiry time
            - Valid URLs return 200 status code
    """
    with patch("app.main.r") as mock_r:
        mock_r.set.return_value = False

        response = client.post("/shorten", json= { "url": "https://google.com" })
        data = response.json()

        assert response.status_code == 200
        mock_r.set.assert_called_once_with(
            f"{data['short_code']}:url",
            data['original_url'],
            nx=True,
            ex=60 * 60 * 24
        )


def test_get_url_metadata(mocker, client: TestClient, fake_redis: FakeRedis):
    """ Test missing URL metadata lookup raises HTTPException """
    test_code = "a9dc2b"
    mock_exists = mocker.patch("app.main.r.exists")
    fake_redis.set(f"url_{test_code}", "https://google.com", nx=True, ex=60*60*24)

    response = client.get(f"/api/urls/{test_code}")
    assert response.json()["clicks"] == 0

    mock_exists.return_value = False

    with pytest.raises(HTTPException):
        get_url_metadata(test_code)


def test_redirect(fake_redis: FakeRedis, client: TestClient):
    """ Test:
        - Valid short code redirects to correct URL
        - URL visit count is incremented
        - Returns HTTP 307 status code
    """
    test_url = "https://google.com"
    fake_code = "sad1sa"
    test_code = "a9dc2b"

    fake_redis.set(f"{test_code}:url", test_url, nx=True, ex=60 * 60 * 24)

    with pytest.raises(HTTPException):
        redirect(fake_code, fake_redis)

    response = client.get(f"/{test_code}", follow_redirects=False)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert fake_redis.get(f"{test_code}:clicks").decode() == "1"


@pytest.mark.parametrize("url", ["https://pofdkgofpgk", "", "http:/google.com"])
def test_url(url: str, client: TestClient):
    """ Test invalid URLs raises HTTP error """
    with pytest.raises(HTTPException, match="Invalid URL"):
        shorten_url(url)