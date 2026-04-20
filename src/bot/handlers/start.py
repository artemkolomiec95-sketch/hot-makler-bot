from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot import texts
from src.bot.keyboards import kb_start
from src.bot.states import SearchFSM

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.WELCOME, parse_mode="HTML", reply_markup=kb_start())


@router.callback_query(lambda c: c.data == "start_search")
async def cb_start_search(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    # Переходим к выбору дат — используем aiogram-calendar
    from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
    await state.set_state(SearchFSM.check_in)
    await callback.message.answer(
        texts.ASK_CHECK_IN,
        parse_mode="HTML",
        reply_markup=await SimpleCalendar().start_calendar(),
    )


@router.callback_query(lambda c: c.data == "restart")
async def cb_restart(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer(texts.WELCOME, parse_mode="HTML", reply_markup=kb_start())
