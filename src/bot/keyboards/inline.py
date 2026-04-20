from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def kb_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔍 Найти жильё", callback_data="start_search")
    ]])


def kb_guests() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1", callback_data="guests:1"),
            InlineKeyboardButton(text="2", callback_data="guests:2"),
            InlineKeyboardButton(text="3", callback_data="guests:3"),
        ],
        [
            InlineKeyboardButton(text="4", callback_data="guests:4"),
            InlineKeyboardButton(text="5", callback_data="guests:5"),
            InlineKeyboardButton(text="6+", callback_data="guests:6"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_districts(districts: list[str], selected: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for d in districts:
        check = "✅ " if d in selected else ""
        buttons.append([InlineKeyboardButton(
            text=f"{check}{d}", callback_data=f"district:{d}"
        )])
    buttons.append([
        InlineKeyboardButton(text="🌍 Любой район", callback_data="district:any"),
        InlineKeyboardButton(text="✔️ Готово", callback_data="district:done"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_rooms() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="rooms:1"),
            InlineKeyboardButton(text="2", callback_data="rooms:2"),
            InlineKeyboardButton(text="3", callback_data="rooms:3"),
        ],
        [
            InlineKeyboardButton(text="4+", callback_data="rooms:4"),
            InlineKeyboardButton(text="Любое", callback_data="rooms:any"),
        ],
    ])


def kb_bathrooms() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="1", callback_data="bathrooms:1"),
        InlineKeyboardButton(text="2+", callback_data="bathrooms:2"),
        InlineKeyboardButton(text="Любое", callback_data="bathrooms:any"),
    ]])


def kb_yes_no_skip(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Нужен(а)", callback_data=f"{prefix}:yes"),
        InlineKeyboardButton(text="➡️ Не важно", callback_data=f"{prefix}:any"),
    ]])


def kb_skip() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➡️ Пропустить", callback_data="budget:skip")
    ]])


def kb_results_nav(has_next: bool, prop_id: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="❤️ Интересно", callback_data=f"want:{prop_id}"),
    ]
    if has_next:
        buttons.append(InlineKeyboardButton(text="➡️ Следующий", callback_data="next"))
    row2 = [InlineKeyboardButton(text="🔙 Изменить критерии", callback_data="restart")]
    return InlineKeyboardMarkup(inline_keyboard=[buttons, row2])


def kb_pdp() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Согласен", callback_data="pdp:agree"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="pdp:cancel"),
    ]])
