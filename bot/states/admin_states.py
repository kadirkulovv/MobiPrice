from aiogram.fsm.state import State, StatesGroup


# --- ADD STATES (CREATE) ---

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
    waiting_for_quantity = State()


# --- EDIT STATES (UPDATE) ---

class BrandEditStates(StatesGroup):
    waiting_for_new_data = State()


class SeriesEditStates(StatesGroup):
    waiting_for_new_name = State()


class PhoneEditStates(StatesGroup):
    waiting_for_new_data = State()


class IssueEditStates(StatesGroup):
    waiting_for_new_data = State()


class ComparisonEditStates(StatesGroup):
    waiting_for_new_price = State()
    waiting_for_new_qty = State()


class DeleteStates(StatesGroup):
    waiting_for_confirm = State()
