from fastapi import HTTPException
import pytest
from main import hash_url, get_url_metadata, shorten_url, redirect

def test_hash_url():
    url = "https://google.com"

    assert len(hash_url(url)) == 6
    assert hash_url(url) == hash_url(url)
    assert hash_url(url) != hash_url(url + "a")

@pytest.mark.parametrize("url", ["https://pofdkgofpgk", "", "http:/google.com"])
def test_url(url: str):
    with pytest.raises(HTTPException, match="Invalid URL"):
        shorten_url(url)