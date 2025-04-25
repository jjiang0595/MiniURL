<img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-005571?logo=fastapi" /> <img src="https://img.shields.io/badge/redis-%23DD0031.svg?logo=redis&logoColor=white" /> <img src="https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white" /><img src="https://img.shields.io/badge/coverage-95%25-brightgreen" /> <img src="https://img.shields.io/badge/k6-7D64FF?logo=k6&logoColor=white" />

# URL-Shortener (FastAPI + Redis)

## 📝 Description
A lightweight URL shortener built with:  
⚡ Python (FastAPI) • 🗃️ Redis • 📊 95%+ Test Coverage

## ⚙️ Installation
```bash 
pip install fastapi uvicorn redis
```

## 🖥️ Usage
```bash
uvicorn main:app --reload 
```

## 🌐 API Reference
```markdown
| Endpoint           | Method | Body               | Example Response                                                                                                                       |
|--------------------|--------|--------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `/api/urls/{code}` | GET    | -                  | `{ "original_url": "https://www.example-website.com/",<br/> "clicks": 0,<br/> "expiry_time": "23:59:59" }`                             |
| `/shorten`         | POST   | `{ "url": "..." }` | `{ "original_url": "https://www.example-website.com/",<br/> "short_url": "http://your_site.com/0OGWoM",<br/> "short_code": "0OGWoM" }` |
| `/{code}`          | GET    | -                  | `307 - Redirect `                                                                                                                      |
```

## 🧪 Tests
**Unit Tests (Pytest)**
- Core Validation
  - URL shortening/redirecting
  - Rate limiting (allow/deny requests, Redis failure handling)

**Load Tests (k6)**
- 20 VUs generating 770 requests for 10 seconds
- 95% of responses <18ms with 0% errors
- Validated: URL shortening/redirects and metadata endpoints