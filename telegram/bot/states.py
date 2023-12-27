from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class RegisterForm(StatesGroup):
    code = State()
    name = State()

class QuestionsForm(StatesGroup):
    pass
