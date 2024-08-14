import re
from datetime import datetime

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from logger import logger
from .states import AddPatientStates


async def send_main_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить пациента")],
            [KeyboardButton(text="📅 Пациенты сегодня"),
             KeyboardButton(text="📊 Статистика за неделю")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)


async def cmd_start(message: types.Message):
    await send_main_menu(message)


async def handle_attempts(
        message: types.Message, state: FSMContext, attempts_key: str, max_attempts: int,
        error_message: str, clear_message: str):
    data = await state.get_data()
    attempts = data.get(attempts_key, 0)

    attempts += 1
    if attempts < max_attempts:
        await state.update_data({attempts_key: attempts})
        await message.answer(f"{error_message} "
                             f"Если вы сделаете ошибку еще {max_attempts - attempts} "
                             f"раз(а), вы будете возвращены в главное меню.")
    else:
        await message.answer(clear_message)
        await state.clear()
        await send_main_menu(message)
    return attempts


async def cmd_add_patient(message: types.Message, state: FSMContext):
    await message.answer("Введите ФИО пациента:")
    await state.set_state(AddPatientStates.ADDING_NAME)


async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()

    if not name or not re.match(r'^[a-zA-Zа-яА-ЯёЁ ]+$', name):
        attempts = await handle_attempts(
            message, state, "name_attempts", 3,
            "⚠️ Имя не может быть пустым или состоять только из пробелов."
            " ФИО может содержать только буквы и пробелы.",
            "⚠️ Вы возвращены в главное меню из-за многократных ошибок при вводе имени."
        )
        if attempts >= 3:
            return
        return

    await state.update_data(full_name=name, name_attempts=0)
    await message.answer("Введите дату рождения пациента (формат: ГГГГ-ММ-ДД):")
    await state.set_state(AddPatientStates.ADDING_BIRTHDATE)


async def process_birthdate(message: types.Message, state: FSMContext, db):
    text = message.text.strip()

    if not text:
        attempts = await handle_attempts(
            message, state, "birthdate_attempts", 3,
            "⚠️ Дата рождения не может быть пустой или состоять только из пробелов.",
            "⚠️ Вы возвращены в главное меню из-за многократных ошибок при вводе даты рождения."
        )
        if attempts >= 3:
            return
        return

    try:
        birth_date = datetime.strptime(text, '%Y-%m-%d').date()
        today = datetime.now().date()

        # Проверка на дату рождения в будущем
        if birth_date > today:
            await message.answer("⚠️ Дата рождения не может быть в будущем. Пожалуйста, введите корректную дату.")
            return

        # Проверка на возраст больше 100 лет
        age = (today - birth_date).days // 365
        if age > 100:
            await message.answer("⚠️ Возраст пациента не может быть больше 100 лет. Попробуйте снова.")
            return

        await state.update_data(birth_date=birth_date, visit_date=today)
        data = await state.get_data()
        await message.answer(
            f"✅ Пациент успешно добавлен!\n\n👤 ФИО: {data['full_name']}\n🎂 Дата рождения: {data['birth_date']}"
        )
        # Передача всех необходимых аргументов в add_patient_to_db
        await add_patient_to_db(data['full_name'], birth_date, today, db)
        await state.clear()
        await send_main_menu(message)
    except ValueError:
        attempts = await handle_attempts(
            message, state, "birthdate_attempts", 3,
            "⚠️ Неправильный формат даты. Пожалуйста, используйте ГГГГ-ММ-ДД.",
            "⚠️ Вы возвращены в главное меню из-за многократных ошибок при вводе даты рождения."
        )
        if attempts >= 3:
            return


async def add_patient_to_db(full_name: str, birth_date: datetime.date, visit_date: datetime.date, db):
    try:
        await db.add_patient(full_name, birth_date, visit_date)
        logger.info(f"Пациент добавлен: {full_name}, Дата рождения: {birth_date}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении пациента {full_name} в базу данных: {e}")


async def process_confirmation(message: types.Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


async def cmd_today_patients(message: types.Message, db):
    logger.info(f"Пользователь {message.from_user.id} запросил список пациентов на сегодня.")
    patients = await db.get_today_patients()
    if patients:
        patient_list = "\n".join([f"👤 {name} (🎂 Дата рождения: {birth_date})" for name, birth_date in patients])
        await message.answer(f"📅 Пациенты, пришедшие сегодня:\n\n{patient_list}")
    else:
        await message.answer("Сегодня нет пациентов.")
    await send_main_menu(message)


async def cmd_week_stats(message: types.Message, db):
    logger.info(f"Пользователь {message.from_user.id} запросил статистику за неделю.")
    stats = await db.get_weekly_stats()
    days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    stats_message = "\n".join([f"📅 {days[int(day)]}: {count} пациентов" for day, count in stats])
    await message.answer(f"📊 Количество пациентов за последние 7 дней:\n\n{stats_message}")
    await send_main_menu(message)


def register_handlers(dp, db):
    async def add_patient_wrapper(message: types.Message, state: FSMContext):
        await cmd_add_patient(message, state)

    async def today_patients_wrapper(message: types.Message):
        await cmd_today_patients(message, db)

    async def week_stats_wrapper(message: types.Message):
        await cmd_week_stats(message, db)

    async def confirmation_wrapper(message: types.Message, state: FSMContext):
        await process_confirmation(message, state)

    async def birthdate_wrapper(message: types.Message, state: FSMContext):
        await process_birthdate(message, state, db)

    dp.message.register(cmd_start, Command(commands=['start']))

    dp.message.register(add_patient_wrapper, Command(commands=['add_patient']))
    dp.message.register(today_patients_wrapper, Command(commands=['today_patients']))
    dp.message.register(week_stats_wrapper, Command(commands=['week_stats']))

    dp.message.register(birthdate_wrapper, AddPatientStates.ADDING_BIRTHDATE)
    dp.message.register(process_name, AddPatientStates.ADDING_NAME)
    dp.message.register(confirmation_wrapper, AddPatientStates.CONFIRMATION)

    dp.message.register(add_patient_wrapper, lambda message: message.text == "➕ Добавить пациента")
    dp.message.register(today_patients_wrapper, lambda message: message.text == "📅 Пациенты сегодня")
    dp.message.register(week_stats_wrapper, lambda message: message.text == "📊 Статистика за неделю")
