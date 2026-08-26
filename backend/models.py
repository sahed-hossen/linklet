from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class URL(Base):
    __tablename__ = "urls"

    short_code = Column(String(10), primary_key=True, index=True)
    client_id = Column(String(64), nullable=True, index=True)
    long_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    clicks = relationship("Click", back_populates="url", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String(10), ForeignKey("urls.short_code"), nullable=False, index=True)
    clicked_at = Column(DateTime, default=utcnow, nullable=False)
    referrer = Column(Text, nullable=True)

    url = relationship("URL", back_populates="clicks")
