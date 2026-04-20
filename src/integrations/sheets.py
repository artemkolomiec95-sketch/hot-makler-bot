from __future__ import annotations

import json
import logging
import os

import gspread
from google.oauth2.service_account import Credentials

from src.core.config import settings
from src.core.models import Property, Lead

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

PROPERTIES_SHEET = "Properties"
LEADS_SHEET = "Leads"


def _get_client() -> gspread.Client:
    sa_json = settings.google_service_account_json
    if os.path.isfile(sa_json):
        creds = Credentials.from_service_account_file(sa_json, scopes=SCOPES)
    else:
        info = json.loads(sa_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def fetch_properties() -> list[Property]:
    if not settings.google_sheets_id:
        logger.warning("GOOGLE_SHEETS_ID не задан, возвращаем тестовые данные")
        return _demo_properties()
    try:
        client = _get_client()
        sheet = client.open_by_key(settings.google_sheets_id)
        ws = sheet.worksheet(PROPERTIES_SHEET)
        records = ws.get_all_records()
        properties = []
        for row in records:
            try:
                prop = Property.model_validate(row)
                properties.append(prop)
            except Exception as e:
                logger.warning(f"Пропускаем строку {row.get('id', '?')}: {e}")
        logger.info(f"Загружено {len(properties)} объектов из Sheets")
        return properties
    except Exception as e:
        logger.error(f"Ошибка загрузки из Sheets: {e}")
        return []


def append_lead(lead: Lead) -> bool:
    if not settings.google_sheets_id:
        logger.info("Sheets не настроен, лид записан только в SQLite")
        return True
    try:
        client = _get_client()
        sheet = client.open_by_key(settings.google_sheets_id)
        try:
            ws = sheet.worksheet(LEADS_SHEET)
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet(LEADS_SHEET, rows=1000, cols=12)
            ws.append_row([
                "timestamp", "client_tg_id", "client_name", "client_contact",
                "property_id", "check_in", "check_out", "guests",
                "total_price", "currency", "status",
            ])
        ws.append_row([
            lead.check_in.strftime("%d/%m/%Y %H:%M"),
            lead.client_tg_id,
            lead.client_name,
            lead.client_contact,
            lead.property_id,
            lead.check_in.strftime("%d/%m/%Y"),
            lead.check_out.strftime("%d/%m/%Y"),
            lead.guests,
            lead.total_price,
            lead.currency,
            lead.status,
        ])
        return True
    except Exception as e:
        logger.error(f"Ошибка записи лида в Sheets: {e}")
        return False


def _demo_properties() -> list[Property]:
    """Тестовые данные когда Sheets не настроен."""
    from datetime import date
    return [
        Property(
            id="A001",
            district="Дуонг-Донг",
            rooms=2,
            has_kitchen=True,
            bathrooms=1,
            has_ac=True,
            max_guests=4,
            price_per_day=55,
            currency="USD",
            photos_url="https://t.me",
            description_ru="Уютные апартаменты в центре Дуонг-Донга. Панорамный вид на море, свежий ремонт.",
            realtor_whatsapp="+84901234567",
            unavailable_dates=[],
            status="active",
        ),
        Property(
            id="A002",
            district="Бай-Чуонг",
            rooms=1,
            has_kitchen=True,
            bathrooms=1,
            has_ac=True,
            max_guests=2,
            price_per_day=35,
            currency="USD",
            photos_url="https://t.me",
            description_ru="Студия в 200 метрах от пляжа Бай-Чуонг. Тихое место, отличный рассвет.",
            realtor_whatsapp="+84901234567",
            unavailable_dates=[],
            status="active",
        ),
        Property(
            id="A003",
            district="Дуонг-Донг",
            rooms=3,
            has_kitchen=True,
            bathrooms=2,
            has_ac=True,
            max_guests=6,
            price_per_day=90,
            currency="USD",
            photos_url="https://t.me",
            description_ru="Просторные 3-комнатные апартаменты для большой компании. Бассейн в здании.",
            realtor_whatsapp="+84901234567",
            unavailable_dates=[(date(2026, 5, 1), date(2026, 5, 10))],
            status="active",
        ),
    ]
