from aiogram.fsm.state import State, StatesGroup

class AddPatientStates(StatesGroup):
    ADDING_NAME = State()
    ADDING_BIRTHDATE = State()
    CONFIRMATION = State()