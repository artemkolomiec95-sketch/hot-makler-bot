from __future__ import annotations

import logging
from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from src.bot import texts
from src.bot.keyboards import (
    kb_guests, kb_districts, kb_rooms, kb_bathrooms,
    kb_yes_no_skip, kb_skip,
)
from src.bot.states import SearchFSM

logger = logging.getLogger(__name__)
router = Router()


# ---------- check_in ----------
@router.callback_query(SimpleCalendarCallback.filter(), SearchFSM.check_in)
async def cb_check_in(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, value = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return
    if value.date() < date.today():
        await callback.answer("Дата не может быть в прошлом", show_alert=True)
        return
    await state.update_data(check_in=value.date().isoformat())
    await state.set_state(SearchFSM.check_out)
    await callback.message.answer(
        texts.ASK_CHECK_OUT,
        parse_mode="HTML",
        reply_markup=await SimpleCalendar().start_calendar(),
    )


# ---------- check_out ----------
@router.callback_query(SimpleCalendarCallback.filter(), SearchFSM.check_out)
async def cb_check_out(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, value = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return
    data = await state.get_data()
    check_in = date.fromisoformat(data["check_in"])
    if value.date() <= check_in:
        await callback.answer("Дата выезда должна быть позже даты заезда", show_alert=True)
        return
    await state.update_data(check_out=value.date().isoformat())
    await state.set_state(SearchFSM.guests)
    await callback.message.answer(texts.ASK_GUESTS, parse_mode="HTML", reply_markup=kb_guests())


# ---------- guests ----------
@router.callback_query(F.data.startswith("guests:"), SearchFSM.guests)
async def cb_guests(callback: CallbackQuery, state: FSMContext):
    guests = int(callback.data.split(":")[1])
    await state.update_data(guests=guests)
    await callback.answer()

    # Загружаем список районов из кэша
    from src.bot.handlers.results import get_properties
    props = await get_properties()
    districts = sorted(set(p.district for p in props))

    await state.update_data(districts_available=districts, districts_selected=[])
    await state.set_state(SearchFSM.districts)
    await callback.message.answer(
        texts.ASK_DISTRICTS,
        parse_mode="HTML",
        reply_markup=kb_districts(districts, []),
    )


# ---------- districts ----------
@router.callback_query(F.data.startswith("district:"), SearchFSM.districts)
async def cb_districts(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected: list[str] = list(data.get("districts_selected", []))
    available: list[str] = data.get("districts_available", [])

    if val == "any":
        selected = []
        await state.update_data(districts_selected=[])
        await callback.answer("Выбраны все районы")
        await state.set_state(SearchFSM.rooms)
        await callback.message.answer(texts.ASK_ROOMS, parse_mode="HTML", reply_markup=kb_rooms())
        return

    if val == "done":
        await callback.answer()
        await state.set_state(SearchFSM.rooms)
        await callback.message.answer(texts.ASK_ROOMS, parse_mode="HTML", reply_markup=kb_rooms())
        return

    if val in selected:
        selected.remove(val)
    else:
        selected.append(val)
    await state.update_data(districts_selected=selected)
    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=kb_districts(available, selected)
    )


# ---------- rooms ----------
@router.callback_query(F.data.startswith("rooms:"), SearchFSM.rooms)
async def cb_rooms(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]
    rooms = None if val == "any" else int(val)
    await state.update_data(rooms=rooms)
    await callback.answer()
    await state.set_state(SearchFSM.bathrooms)
    await callback.message.answer(texts.ASK_BATHROOMS, parse_mode="HTML", reply_markup=kb_bathrooms())


# ---------- bathrooms ----------
@router.callback_query(F.data.startswith("bathrooms:"), SearchFSM.bathrooms)
async def cb_bathrooms(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]
    bathrooms = None if val == "any" else int(val)
    await state.update_data(bathrooms=bathrooms)
    await callback.answer()
    await state.set_state(SearchFSM.kitchen)
    await callback.message.answer(
        texts.ASK_KITCHEN, parse_mode="HTML",
        reply_markup=kb_yes_no_skip("kitchen"),
    )


# ---------- kitchen ----------
@router.callback_query(F.data.startswith("kitchen:"), SearchFSM.kitchen)
async def cb_kitchen(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]
    need_kitchen = True if val == "yes" else None
    await state.update_data(need_kitchen=need_kitchen)
    await callback.answer()
    await state.set_state(SearchFSM.ac)
    await callback.message.answer(
        texts.ASK_AC, parse_mode="HTML",
        reply_markup=kb_yes_no_skip("ac"),
    )


# ---------- ac ----------
@router.callback_query(F.data.startswith("ac:"), SearchFSM.ac)
async def cb_ac(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]
    need_ac = True if val == "yes" else None
    await state.update_data(need_ac=need_ac)
    await callback.answer()
    await state.set_state(SearchFSM.budget)
    await callback.message.answer(
        texts.ASK_BUDGET, parse_mode="HTML",
        reply_markup=kb_skip(),
    )


# ---------- budget: skip ----------
@router.callback_query(F.data == "budget:skip", SearchFSM.budget)
async def cb_budget_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(budget_min=None, budget_max=None)
    await callback.answer()
    await _run_search(callback.message, state)


# ---------- budget: text input ----------
@router.message(SearchFSM.budget)
async def msg_budget(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) == 2:
        try:
            bmin, bmax = float(parts[0]), float(parts[1])
            if bmin < bmax:
                await state.update_data(budget_min=bmin, budget_max=bmax)
                await _run_search(message, state)
                return
        except ValueError:
            pass
    await message.answer(texts.BUDGET_INVALID, parse_mode="HTML", reply_markup=kb_skip())


async def _run_search(msg, state: FSMContext):
    from src.bot.handlers.results import show_results
    await msg.answer(texts.SEARCHING)
    await show_results(msg, state, index=0)
