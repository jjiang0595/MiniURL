import redis
from fastapi import FastAPI
from starlette.responses import RedirectResponse

app = FastAPI()
r = redis.Redis(host='localhost', port=6379)

url_db = {}

@app.get("/")
def get_url_db():
     return url_db

@app.post("/shorten")
def shorten_url(url: str):
     short_code = str(hash(url))[:6]
     url_db[short_code] = url
     return {"Shortened URL: ", short_code}

@app.get("/{url_code}")
def redirect(url_code: str):
     return RedirectResponse(url_db.get(url_code))


