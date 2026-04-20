from __future__ import annotations

import logging
import urllib.parse
from typing import Protocol

from src.core.models import Lead, SendResult

logger = logging.getLogger(__name__)


class WhatsAppNotifier(Protocol):
    async def send_lead(self, lead: Lead) -> SendResult: ...


def _build_wa_link(lead: Lead) -> str:
    nights = (lead.check_out - lead.check_in).days
    text = (
        f"Có yêu cầu thuê từ {lead.guests} khách,\n"
        f"từ ngày {lead.check_in.strftime('%d/%m/%Y')} đến ngày {lead.check_out.strftime('%d/%m/%Y')} ({nights} đêm),\n"
        f"cho bất động sản: {lead.property_id} — {lead.district}, {lead.rooms} phòng.\n"
        f"Giá đã thỏa thuận cho toàn bộ thời gian: {lead.total_price} {lead.currency}\n"
        f"({lead.price_per_day} {lead.currency}/ngày × {nights} ngày).\n\n"
        f"Thông tin khách hàng:\n"
        f"— Tên: {lead.client_name}\n"
        f"— Liên hệ: {lead.client_contact}"
    )
    encoded = urllib.parse.quote(text)
    phone = lead.realtor_whatsapp.replace("+", "").replace(" ", "")
    return f"https://wa.me/{phone}?text={encoded}"


class TelegramFallbackNotifier:
    """MVP: уведомление риелтору в Telegram + wa.me ссылка одним тапом."""

    def __init__(self, bot, realtor_tg_id: int):
        self.bot = bot
        self.realtor_tg_id = realtor_tg_id

    async def send_lead(self, lead: Lead) -> SendResult:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        nights = (lead.check_out - lead.check_in).days
        text = (
            f"📋 <b>Новая заявка на аренду</b>\n\n"
            f"🏠 Объект: <b>{lead.property_id}</b> — {lead.district}\n"
            f"🛏 Комнат: {lead.rooms}\n"
            f"👥 Гостей: {lead.guests}\n"
            f"📅 {lead.check_in.strftime('%d.%m.%Y')} → {lead.check_out.strftime('%d.%m.%Y')} ({nights} ночей)\n"
            f"💵 Итого: <b>{lead.total_price} {lead.currency}</b>\n\n"
            f"👤 Клиент: <b>{lead.client_name}</b>\n"
            f"📞 Контакт: {lead.client_contact}"
        )
        wa_link = _build_wa_link(lead)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="💬 Открыть WhatsApp", url=wa_link)
        ]])
        try:
            await self.bot.send_message(
                self.realtor_tg_id,
                text,
                parse_mode="HTML",
                reply_markup=kb,
            )
            return SendResult(ok=True)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления риелтору: {e}")
            return SendResult(ok=False, error=str(e))
