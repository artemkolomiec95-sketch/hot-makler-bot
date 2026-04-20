from __future__ import annotations

import logging
from datetime import date, datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot import texts
from src.bot.keyboards import kb_pdp
from src.bot.states import ContactFSM
from src.core.models import Lead
from src.core.pricing import calc_total

logger = logging.getLogger(__name__)
router = Router()


@router.message(ContactFSM.name)
async def msg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Введите имя (не менее 2 символов):")
        return
    await state.update_data(client_name=name)
    await state.set_state(ContactFSM.contact)
    await message.answer(texts.ASK_CONTACT, parse_mode="HTML")


@router.message(ContactFSM.contact)
async def msg_contact(message: Message, state: FSMContext):
    contact = message.text.strip()
    await state.update_data(client_contact=contact)
    await state.set_state(ContactFSM.confirm_pdp)
    await message.answer(texts.PDP_TEXT, parse_mode="HTML", reply_markup=kb_pdp())


@router.callback_query(F.data == "pdp:cancel", ContactFSM.confirm_pdp)
async def cb_pdp_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    from src.bot.keyboards import kb_start
    await callback.message.answer("Заявка отменена. Нажмите /start для нового поиска.", reply_markup=kb_start())


@router.callback_query(F.data == "pdp:agree", ContactFSM.confirm_pdp)
async def cb_pdp_agree(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()

    # Собираем лид
    from src.bot.handlers.results import get_properties
    properties = await get_properties()
    prop_id = data["chosen_property_id"]
    prop = next((p for p in properties if p.id == prop_id), None)

    if not prop:
        await callback.message.answer("Ошибка: объект не найден. Попробуйте /start")
        await state.clear()
        return

    check_in = date.fromisoformat(data["check_in"])
    check_out = date.fromisoformat(data["check_out"])
    from src.core.models import SearchCriteria
    criteria = SearchCriteria(
        check_in=check_in, check_out=check_out,
        guests=data["guests"],
    )
    total = calc_total(prop, criteria)

    lead = Lead(
        client_tg_id=callback.from_user.id,
        client_name=data["client_name"],
        client_contact=data["client_contact"],
        property_id=prop.id,
        district=prop.district,
        rooms=prop.rooms,
        check_in=check_in,
        check_out=check_out,
        guests=data["guests"],
        total_price=total,
        currency=prop.currency,
        price_per_day=prop.price_per_day,
        realtor_whatsapp=prop.realtor_whatsapp,
    )

    # Сохраняем в SQLite
    from src.storage.db import SessionLocal
    from src.storage.repositories import LeadRepo
    async with SessionLocal() as session:
        await LeadRepo(session).save(lead)

    # Пишем в Google Sheets
    import asyncio
    from src.integrations.sheets import append_lead
    await asyncio.get_event_loop().run_in_executor(None, append_lead, lead)

    # Отправляем риелтору
    from aiogram import Bot
    from src.core.config import settings
    from src.integrations.whatsapp import TelegramFallbackNotifier

    bot: Bot = callback.bot
    notifier = TelegramFallbackNotifier(bot, settings.realtor_tg_id)
    result = await notifier.send_lead(lead)

    await state.clear()
    if result.ok:
        await callback.message.answer(texts.LEAD_SENT, parse_mode="HTML")
    else:
        await callback.message.answer(texts.LEAD_FAILED, parse_mode="HTML")
