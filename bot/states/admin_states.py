from aiogram.fsm.state import State, StatesGroup


class BrandAddStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_logo = State()


class SeriesAddStates(StatesGroup):
    waiting_for_brand = State()
    waiting_for_name = State()


class PhoneAddStates(StatesGroup):
    waiting_for_brand = State()
    waiting_for_series = State()
    waiting_for_name = State()
    waiting_for_image = State()


class IssueAddStates(StatesGroup):
    waiting_for_brand = State()
    waiting_for_series = State()
    waiting_for_phone = State()
    waiting_for_title = State()
    waiting_for_icon = State()


class ComparisonAddStates(StatesGroup):
    waiting_for_brand = State()
    waiting_for_series = State()
    waiting_for_phone = State()
    waiting_for_issue = State()
    waiting_for_quality = State()
    waiting_for_price = State()


class DeleteStates(StatesGroup):
    waiting_for_confirm = State()
