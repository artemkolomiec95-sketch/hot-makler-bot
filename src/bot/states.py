from aiogram.fsm.state import State, StatesGroup


class SearchFSM(StatesGroup):
    check_in = State()
    check_out = State()
    guests = State()
    districts = State()
    rooms = State()
    bathrooms = State()
    kitchen = State()
    ac = State()
    budget = State()
    results = State()


class ContactFSM(StatesGroup):
    name = State()
    contact = State()
    confirm_pdp = State()
