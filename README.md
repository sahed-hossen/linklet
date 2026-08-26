# Linklet ⚡

[![CI](https://github.com/sahed-hossen/linklet/actions/workflows/ci.yml/badge.svg)](https://github.com/sahed-hossen/linklet/actions/workflows/ci.yml)
[![Deploy to Render](https://github.com/sahed-hossen/linklet/actions/workflows/deploy.yml/badge.svg)](https://github.com/sahed-hossen/linklet/actions/workflows/deploy.yml)

A modern, lightweight URL shortener built with **FastAPI** and **Supabase (PostgreSQL)**. Features a minimal obsidian dark UI, instant QR code rendering, click analytics, custom aliases, and link expiration — with zero external frontend framework dependencies.

---

## ✨ Features

- **Instant URL Shortening** — Generates clean Base62 7-character IDs or custom aliases (up to 10 chars)
- **Click & Referrer Tracking** — Logs timestamped click metrics and referrer domains per link
- **Link Expiration & Deactivation** — Scheduled expiry timestamps and one-click soft deactivation
- **Dynamic QR Code Generation** — In-browser QR rendering with high-resolution canvas output
- **Obsidian Dark UI** — Pure AMOLED black theme with smooth micro-animations
- **Unified Architecture** — FastAPI serves the REST API and static frontend from a single process

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy, Pydantic v2, Uvicorn |
| Database | Supabase (PostgreSQL) via `psycopg2-binary` |
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES6+), QRCode.js |
| Testing | pytest, Starlette TestClient, httpx2 |
| CI/CD | GitHub Actions → Render |

---

## 📁 Project Structure

```
linklet/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Run tests on every push / PR
│       └── deploy.yml      # Deploy to Render when main passes CI
├── .env.example            # Template — copy to backend/.env and fill in values
├── render.yaml             # Render web service configuration
├── backend/
│   ├── __init__.py
│   ├── main.py             # FastAPI app: routes + static file handlers
│   ├── database.py         # Supabase engine + session dependency
│   ├── models.py           # SQLAlchemy ORM models (URL, Click)
│   ├── id_generator.py     # Base62 random short code generator
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Single-page dashboard
│   ├── style.css           # Design tokens & responsive styles
│   └── app.js              # Async API client
└── tests/
    ├── conftest.py         # Shared pytest fixtures (clean_db, SQLite override)
    └── test_api.py         # Full API test suite (8 tests)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- A [Supabase](https://supabase.com) account (free tier works)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/sahed-hossen/linklet.git
cd linklet
```

### 2. Install dependencies

```bash
py -m pip install -r backend/requirements.txt
```

### 3. Configure environment variables

```bash
copy .env.example backend\.env
```

Open `backend/.env` and fill in your Supabase connection string:

```env
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[HOST]:5432/postgres
```

> **Where to find it:** Supabase Dashboard → Project Settings → Database → Connection string → URI
> Use port **5432** (session-mode pooler), not 6543.

### 4. Run the development server

```bash
cd backend
py -m uvicorn main:app --reload
```

| Endpoint | URL |
|---|---|
| Web Dashboard | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 🧪 Running Tests

Tests use an isolated SQLite database — no Supabase credentials required:

```bash
py -m pytest tests/ -v
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/shorten` | Shorten a URL (`long_url`, optional `custom_alias`, optional `expires_at`) |
| `GET` | `/{short_code}` | Redirect to destination + log click & referrer |
| `GET` | `/api/links` | List all links with click counts and status |
| `GET` | `/api/links/{code}/stats` | Full analytics + 100 most recent clicks |
| `DELETE` | `/api/links/{code}` | Soft-deactivate a link (`is_active = false`) |

---

## ⚙️ CI/CD Pipeline

```
Push to any branch  →  CI (pytest)  →  ✅ / ❌
Push to main        →  CI (pytest)  →  ✅  →  Deploy to Render
```

The deploy step is gated behind CI — a failing test will never reach production.

**Required GitHub Secret:**

| Secret | Value |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Your Render service deploy hook URL |

---

## 🌐 Deploying to Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect this repository — Render will auto-detect `render.yaml`
3. Set the `DATABASE_URL` environment variable to your Supabase URI
4. Copy the **Deploy Hook URL** (Service → Settings → Deploy Hook)
5. Add it as `RENDER_DEPLOY_HOOK_URL` in GitHub → Settings → Secrets → Actions

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
