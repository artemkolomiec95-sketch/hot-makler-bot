from __future__ import annotations

import logging
from datetime import date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from src.bot import texts
from src.bot.keyboards import kb_results_nav
from src.bot.states import SearchFSM
from src.core.models import Property, SearchCriteria
from src.core.search import search_with_fallback
from src.core.pricing import calc_total

logger = logging.getLogger(__name__)
router = Router()

# Глобальный кэш объектов (заполняется при старте и синхронизации)
_properties_cache: list[Property] = []


def update_cache(properties: list[Property]):
    global _properties_cache
    _properties_cache = properties
    logger.info(f"Кэш обновлён: {len(properties)} объектов")


async def get_properties() -> list[Property]:
    return _properties_cache


def _build_criteria(data: dict) -> SearchCriteria:
    return SearchCriteria(
        check_in=date.fromisoformat(data["check_in"]),
        check_out=date.fromisoformat(data["check_out"]),
        guests=data["guests"],
        districts=data.get("districts_selected") or [],
        rooms=data.get("rooms"),
        bathrooms=data.get("bathrooms"),
        need_kitchen=data.get("need_kitchen"),
        need_ac=data.get("need_ac"),
        budget_min=data.get("budget_min"),
        budget_max=data.get("budget_max"),
    )


def _format_card(prop: Property, criteria: SearchCriteria) -> str:
    nights = criteria.nights
    total = calc_total(prop, criteria)
    kitchen_line = "\n🍳 Кухня" if prop.has_kitchen else ""
    ac_line = "  |  ❄️ Кондиционер" if prop.has_ac else ""
    return texts.PROPERTY_CARD.format(
        id=prop.id,
        district=prop.district,
        rooms=prop.rooms,
        max_guests=prop.max_guests,
        bathrooms=prop.bathrooms,
        kitchen_line=kitchen_line,
        ac_line=ac_line,
        check_in=criteria.check_in.strftime("%d.%m.%Y"),
        check_out=criteria.check_out.strftime("%d.%m.%Y"),
        nights=nights,
        total_price=total,
        price_per_day=prop.price_per_day,
        description_ru=prop.description_ru,
    )


async def show_results(msg: Message, state: FSMContext, index: int = 0):
    data = await state.get_data()
    criteria = _build_criteria(data)
    properties = await get_properties()

    results, fallback_note = search_with_fallback(properties, criteria)

    if not results:
        await state.set_state(None)
        await msg.answer(texts.NO_RESULTS, parse_mode="HTML")
        return

    await state.update_data(result_ids=[p.id for p in results])
    await state.set_state(SearchFSM.results)

    if fallback_note:
        await msg.answer(f"ℹ️ {fallback_note}", parse_mode="HTML")

    await _send_card(msg, results, index, criteria, state)


async def _send_card(msg: Message, results: list[Property], index: int, criteria: SearchCriteria, state: FSMContext):
    await state.update_data(result_index=index)
    prop = results[index]
    has_next = index < len(results) - 1
    caption = _format_card(prop, criteria)
    kb = kb_results_nav(has_next, prop.id)

    await msg.answer(
        f"📋 <b>Вариант {index + 1} из {len(results)}</b>\n\n{caption}",
        parse_mode="HTML",
        reply_markup=kb,
        disable_web_page_preview=False,
    )


# ---------- next ----------
@router.callback_query(F.data == "next", SearchFSM.results)
async def cb_next(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    index = data.get("result_index", 0) + 1
    result_ids: list[str] = data.get("result_ids", [])
    properties = await get_properties()
    results = [p for p in properties if p.id in result_ids]
    results.sort(key=lambda p: result_ids.index(p.id))

    if index >= len(results):
        await callback.message.answer("Это были все варианты. Нажмите /start для нового поиска.")
        return

    criteria = _build_criteria(data)
    await _send_card(callback.message, results, index, criteria, state)


# ---------- want ----------
@router.callback_query(F.data.startswith("want:"), SearchFSM.results)
async def cb_want(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    prop_id = callback.data.split(":", 1)[1]
    await state.update_data(chosen_property_id=prop_id)
    from src.bot.states import ContactFSM
    await state.set_state(ContactFSM.name)
    await callback.message.answer(texts.ASK_NAME, parse_mode="HTML")
