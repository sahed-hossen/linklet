# Linklet ⚡

A modern, lightweight, and high-performance URL shortener built with **FastAPI**, **SQLAlchemy**, and **SQLite**. Designed with a minimal obsidian dark UI, instant QR code rendering, click analytics, and zero external frontend framework dependencies.

---

## ✨ Features

- **Instant URL Shortening**: Generates clean Base62 7-character IDs or supports custom aliases.
- **Click & Referrer Tracking**: Logs timestamped click metrics, visit frequency, and referrer domains.
- **Link Expiration & Deactivation**: Supports scheduled expiry timestamps and one-click soft deactivation.
- **Dynamic QR Code Generation**: In-browser QR code rendering with high-resolution canvas output.
- **Obsidian Dark & Minimal UI**: Pure AMOLED black theme with smooth micro-animations and zero clutter.
- **Unified Single-Process Architecture**: FastAPI serves both the high-performance REST API and the static frontend simultaneously.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pydantic v2, Uvicorn
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+), QRCode.js
- **Testing**: pytest, Starlette TestClient

---

## 📁 Repository Structure

```
Linklet/
├── backend/
│   ├── main.py           # FastAPI application routes & static file handlers
│   ├── database.py       # SQLite engine initialization & session dependency
│   ├── models.py         # SQLAlchemy ORM models (URL, Click)
│   ├── id_generator.py   # Base62 random short code generator
│   └── requirements.txt  # Python package dependencies
├── frontend/
│   ├── index.html        # Dashboard single-page application
│   ├── style.css         # Design tokens & responsive styles
│   └── app.js           # Frontend client & asynchronous API handler
├── tests/
│   └── test_api.py       # Automated pytest test suite
├── .gitignore            # Git ignore configuration
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- Git

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/linklet.git
cd linklet
pip install -r backend/requirements.txt
```

### 3. Run the Development Server

From the project root:

```bash
py -m uvicorn main:app --app-dir backend --reload --port 8000
```

- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Run Automated Tests

```bash
pytest tests/
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/shorten` | Shortens a URL (`long_url`, optional `custom_alias`, optional `expires_at`) |
| `GET` | `/{short_code}` | Logs click event + referrer header and redirects (`302`) to the destination |
| `GET` | `/api/links` | Returns all links with click counts and active statuses |
| `GET` | `/api/links/{code}/stats` | Returns comprehensive link analytics and the 100 most recent click logs |
| `DELETE` | `/api/links/{code}` | Deactivates a short link (`is_active = False`) |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
