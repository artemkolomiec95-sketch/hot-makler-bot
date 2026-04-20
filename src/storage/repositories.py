from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Property, Lead
from .db import PropertyCache, LeadRecord


class PropertyRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_all(self, properties: list[Property]) -> None:
        await self.session.execute(delete(PropertyCache))
        for prop in properties:
            record = PropertyCache(
                id=prop.id,
                data_json=prop.model_dump_json(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(record)
        await self.session.commit()

    async def get_all(self) -> list[Property]:
        result = await self.session.execute(select(PropertyCache))
        rows = result.scalars().all()
        properties = []
        for row in rows:
            try:
                data = json.loads(row.data_json)
                properties.append(Property.model_validate(data))
            except Exception:
                continue
        return properties


class LeadRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, lead: Lead) -> LeadRecord:
        record = LeadRecord(
            client_tg_id=lead.client_tg_id,
            client_name=lead.client_name,
            client_contact=lead.client_contact,
            property_id=lead.property_id,
            check_in=lead.check_in.isoformat(),
            check_out=lead.check_out.isoformat(),
            guests=lead.guests,
            total_price=lead.total_price,
            currency=lead.currency,
            status=lead.status,
        )
        self.session.add(record)
        await self.session.commit()
        return record
