from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator


class Property(BaseModel):
    id: str
    district: str
    rooms: int
    has_kitchen: bool
    bathrooms: int
    has_ac: bool
    max_guests: int
    price_per_day: float
    currency: str = "USD"
    photos_url: str
    description_ru: str
    realtor_whatsapp: str
    unavailable_dates: list[tuple[date, date]] = []
    status: str = "active"

    @field_validator("unavailable_dates", mode="before")
    @classmethod
    def parse_unavailable_dates(cls, v: str | list) -> list[tuple[date, date]]:
        if isinstance(v, list):
            return v
        if not v or not v.strip():
            return []
        result = []
        for period in v.split(","):
            period = period.strip()
            if not period:
                continue
            parts = period.split(":")
            if len(parts) == 2:
                try:
                    start = date.fromisoformat(parts[0].strip())
                    end = date.fromisoformat(parts[1].strip())
                    result.append((start, end))
                except ValueError:
                    continue
        return result

    @field_validator("has_kitchen", "has_ac", mode="before")
    @classmethod
    def parse_bool(cls, v) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().upper() in ("TRUE", "1", "ДА", "YES")
        return bool(v)


class SearchCriteria(BaseModel):
    check_in: date
    check_out: date
    guests: int
    districts: list[str] = []       # пустой = любой
    rooms: Optional[int] = None      # None = любое
    bathrooms: Optional[int] = None
    need_kitchen: Optional[bool] = None
    need_ac: Optional[bool] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days


class Lead(BaseModel):
    client_tg_id: int
    client_name: str
    client_contact: str
    property_id: str
    district: str
    rooms: int
    check_in: date
    check_out: date
    guests: int
    total_price: float
    currency: str
    price_per_day: float
    realtor_whatsapp: str
    status: str = "sent"


class SendResult(BaseModel):
    ok: bool
    error: str = ""
