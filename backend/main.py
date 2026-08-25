from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from id_generator import generate_short_code
from models import Click, URL

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Linklet API",
    description="URL shortener service with analytics and QR code generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serve(filename: str, media_type: Optional[str] = None):
    path = FRONTEND_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    return FileResponse(path, media_type=media_type) if media_type else FileResponse(path)


@app.get("/", include_in_schema=False)
def serve_index():
    return _serve("index.html")


@app.get("/style.css", include_in_schema=False)
def serve_css():
    return _serve("style.css", "text/css")


@app.get("/app.js", include_in_schema=False)
def serve_js():
    return _serve("app.js", "application/javascript")


# --- Schemas ---

class ShortenRequest(BaseModel):
    long_url: str = Field(..., description="Target URL")
    custom_alias: Optional[str] = Field(None, max_length=10)
    expires_at: Optional[datetime] = None

    @field_validator("long_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip()
        if len(v) > 10:
            raise ValueError("Alias must be 10 characters or less")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Alias may only contain letters, numbers, dashes, and underscores")
        return v


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class ClickItem(BaseModel):
    id: int
    clicked_at: datetime
    referrer: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class LinkStatsResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    is_active: bool
    recent_clicks: List[ClickItem]


# --- Helpers ---

def get_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_short_url(request: Request, code: str) -> str:
    return f"{str(request.base_url).rstrip('/')}/{code}"


def serialize_link(request: Request, link: URL) -> LinkResponse:
    return LinkResponse(
        short_code=link.short_code,
        short_url=get_short_url(request, link.short_code),
        long_url=link.long_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        click_count=link.click_count,
        is_active=link.is_active,
    )


# --- Endpoints ---

@app.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
def shorten_url(payload: ShortenRequest, request: Request, db: Session = Depends(get_db)):
    if payload.custom_alias:
        if db.query(URL).filter(URL.short_code == payload.custom_alias).first():
            raise HTTPException(status_code=409, detail="Alias is already in use")
        code = payload.custom_alias
    else:
        code = None
        for _ in range(5):
            candidate = generate_short_code()
            if not db.query(URL).filter(URL.short_code == candidate).first():
                code = candidate
                break
        if not code:
            raise HTTPException(status_code=500, detail="Could not generate a unique code")

    expires = payload.expires_at.replace(tzinfo=None) if payload.expires_at else None
    link = URL(
        short_code=code,
        long_url=payload.long_url,
        created_at=get_now(),
        expires_at=expires,
        click_count=0,
        is_active=True,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return ShortenResponse(
        short_code=link.short_code,
        short_url=get_short_url(request, link.short_code),
        long_url=link.long_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


@app.get("/api/links", response_model=List[LinkResponse])
def list_links(request: Request, db: Session = Depends(get_db)):
    links = db.query(URL).order_by(desc(URL.created_at)).all()
    return [serialize_link(request, l) for l in links]


@app.get("/api/links/{short_code}/stats", response_model=LinkStatsResponse)
def get_link_stats(short_code: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(URL).filter(URL.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    clicks = (
        db.query(Click)
        .filter(Click.short_code == short_code)
        .order_by(desc(Click.clicked_at))
        .limit(100)
        .all()
    )
    return LinkStatsResponse(
        short_code=link.short_code,
        short_url=get_short_url(request, link.short_code),
        long_url=link.long_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        click_count=link.click_count,
        is_active=link.is_active,
        recent_clicks=[ClickItem.model_validate(c) for c in clicks],
    )


@app.delete("/api/links/{short_code}")
def delete_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(URL).filter(URL.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    link.is_active = False
    db.commit()
    return {"message": "Link deactivated", "short_code": short_code}


@app.get("/{short_code}", response_class=RedirectResponse)
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(URL).filter(URL.short_code == short_code).first()
    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Link not found or deactivated")

    if link.expires_at and link.expires_at < get_now():
        raise HTTPException(status_code=404, detail="Link has expired")

    link.click_count += 1
    referrer = request.headers.get("referer") or request.headers.get("referrer")
    db.add(Click(short_code=short_code, clicked_at=get_now(), referrer=referrer))
    db.commit()

    return RedirectResponse(url=link.long_url, status_code=status.HTTP_302_FOUND)
