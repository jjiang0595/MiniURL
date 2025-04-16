# URL-Shortener (FastAPI + Redis)

## 📝 Description
A lightweight URL shortener built with Python (FastAPI) and Redis.

## 🚀 Features
- `POST /shorten?url=<your_url>`: Takes in an url and returns a 6-character code
* `GET /{code}` - Redirects the user to the URL

## ⚙️ Installation
`pip install fastapi uvicorn redis`

## 🖥️ Usage
`uvicorn main:app --reload`

## 🧪 Tests
WIP