import pytest
from fakeredis import FakeRedis
from fastapi import HTTPException, status
from app.main import hash_url, shorten_url, get_url_metadata, app, get_redis
from fastapi.testclient import TestClient


@pytest.fixture
def fake_redis():
    """ Initialize FakeRedis with teardown """
    r = FakeRedis()
    yield r
    r.flushall()


@pytest.fixture
def client(fake_redis):
    """ Initialize FastAPI TestClient with Redis override """
    app.dependency_overrides[get_redis] = lambda: fake_redis
    yield TestClient(app)
    app.dependency_overrides = {}


def test_hash_url():
    """ Test hash validity & uniqueness """
    url = "https://google.com"

    assert len(hash_url(url)) == 6
    assert hash_url(url) == hash_url(url)
    assert hash_url(url) != hash_url(url + "a")


def test_get_url_metadata(mocker):
    """ Test missing URL metadata lookup raises HTTPException """
    test_code = "a9dc2b"
    mock_exists = mocker.patch("app.main.r.exists")

    mock_exists.return_value = False

    with pytest.raises(HTTPException):
        get_url_metadata(test_code)


def test_redirect(fake_redis, client):
    """ Test:
        - Valid short code redirects to correct URL
        - URL visit count is incremented
        - Returns HTTP 307 status code
    """
    test_url = "https://google.com"
    test_code = "a9dc2b"
    fake_redis.set(f"{test_code}:url", test_url, nx=True, ex=60 * 60 * 24)

    response = client.get(f"/{test_code}", follow_redirects=False)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert fake_redis.get(f"{test_code}:clicks").decode() == "1"


@pytest.mark.parametrize("url", ["https://pofdkgofpgk", "", "http:/google.com"])
def test_url(url: str):
    """ Test invalid URLs raises HTTP error """
    with pytest.raises(HTTPException, match="Invalid URL"):
        shorten_url(url)