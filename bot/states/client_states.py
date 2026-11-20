from aiogram.fsm.state import State, StatesGroup


class LoginAuthStates(StatesGroup):
    waiting_for_phone = State()


class CourierLocationStates(StatesGroup):
    waiting_for_location = State()

