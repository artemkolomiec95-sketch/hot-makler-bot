import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, Text
from datetime import datetime

os.makedirs("data", exist_ok=True)

from src.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class PropertyCache(Base):
    __tablename__ = "property_cache"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    data_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LeadRecord(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    client_tg_id: Mapped[int] = mapped_column(Integer)
    client_name: Mapped[str] = mapped_column(String)
    client_contact: Mapped[str] = mapped_column(String)
    property_id: Mapped[str] = mapped_column(String)
    check_in: Mapped[str] = mapped_column(String)
    check_out: Mapped[str] = mapped_column(String)
    guests: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="USD")
    status: Mapped[str] = mapped_column(String, default="sent")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
