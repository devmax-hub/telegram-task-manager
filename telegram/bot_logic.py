import asyncio
import logging
import os
from .views import *
from .models import POSITION_CHOICES, LEVEL_CHOICES
from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher, html, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from babel.dates import format_datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.conf import settings

load_dotenv()

TOKEN = os.getenv('TOKEN')

storage = MemoryStorage()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

router = Router()
dp.include_router(router)

SAVE_DIR = 'downloads'

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

isAdmin = False
employee_id = -1

employee_level = ''
employee_position = ''

# https://www.youtube.com/watch?v=yetfif4j_go
# btnMain - KeyboardButton("Главное меню")
# btnRandon - KeyboardButton("Рандомное число")
# btnother = KeyboardButton(* - Другое*)
# mainMenu - ReplykeyboardMarkup(resize keyboard - True) .add (btnRandon, btnother)
# Samnor Moni
# btnInfo - KeyboardButton (* # Информация")
# btnMoney = KeyboardButton (* « Курсы валют")
# otherMenu - ReplykeyboardMarkup(resize keyboard - True).add(btnInfo, btnMoney, btaMain)

async def send_message_to_employee(chat_id: str, message: str):
    await bot.send_message(chat_id=chat_id, text=message)


def get_employees_to_notify(employee_id: int):
    return Employee.objects.filter(
        id=employee_id,
        role__in=['marketer', 'admin'],
        chat_id__isnull=False
    )


async def notify_employees(employee_id: int, message: str):
    employees = get_employees_to_notify(employee_id)
    for employee in employees:
        await send_message_to_employee(employee.chat_id, message)


registration_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Зарегистрироваться', callback_data='registration')],
])


async def notify_employee(employee_id: int, message: str):
    employee = Employee.objects.get(id=employee_id)
    await bot.send_message(chat_id=chat_id, text=message)


async def notify_marketer(message: str):
    marketer_chat_ids = await get_marketer_chatid()
    for id in marketer_chat_ids:
        await store_notification(id, message)
        await bot.send_message(chat_id=id, text=message)


def get_level_keyboard() -> InlineKeyboardMarkup:
    level_kb = InlineKeyboardBuilder()

    for level in LEVEL_CHOICES:
        level_kb.add(InlineKeyboardButton(text=level[1], callback_data=f'get_level_{level[0]}'))

    level_kb.adjust(*[1] * 10)
    return level_kb.as_markup(resize_keyboard=True)


def get_position_keyboard() -> InlineKeyboardMarkup:
    position_keyboard = InlineKeyboardBuilder()

    for position in POSITION_CHOICES:
        if position[0] not in ['admin', 'marketer']:
            position_keyboard.add(InlineKeyboardButton(text=position[1], callback_data=f'get_position_{position[0]}'))

    position_keyboard.adjust(*[1] * 10)
    return position_keyboard.as_markup(resize_keyboard=True)


main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Вернуться на главную", callback_data="main_menu")],
])

main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Главное меню", callback_data="init_menu")],
    [InlineKeyboardButton(text="Старт/Стоп", callback_data="online")],
    [InlineKeyboardButton(text="Текущие задачи", callback_data="tasks")],
    [InlineKeyboardButton(text="Личный кабинет", callback_data="profile")],
])

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить новую задачу", callback_data="add_task")],
    [InlineKeyboardButton(text="Текущие задачи", callback_data="all_current_tasks")],
    [InlineKeyboardButton(text="Выполненные задачи", callback_data="all_done_tasks")],
    # [InlineKeyboardButton(text="Управление счетами", callback_data="balance_manage")],
    # [InlineKeyboardButton(text="Обнулить счет сотрудника", callback_data="null_money")],
])

profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Выполненные задачи", callback_data="done_tasks")],
    [InlineKeyboardButton(text="Запросить вывод средств", callback_data="get_money")],
])

back_button = InlineKeyboardButton(text="Назад", callback_data="back")
panel_button = InlineKeyboardButton(text="Панель", callback_data="panel")
skip_button = KeyboardButton(text="Пропустить", callback_data="skip")


class InitStates(StatesGroup):
    employee_id = State()
    isAdmin = State()
    employee_position = State()
    employee_level = State()
    isOnline = State()

class AddTaskStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_filePath = State()
    waiting_for_link = State()


class RegistrationStates(StatesGroup):
    waiting_for_iin = State()
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_middlename = State()
    waiting_for_phone = State()
    waiting_for_level = State()
    waiting_for_position = State()


@dp.callback_query(F.data == 'start_menu')
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    employee = await employee_by_telegram(message.from_user.username)
    logging.info(f'employee: {employee}')
    if employee and employee != "employee is not confirmed":
        await state.update_data(employee_id=employee['id'])
        if employee['position'] == 'admin' or employee['position'] == 'marketer':
            isAdmin = employee['position'] in ['admin', 'marketer']
            await state.update_data(isAdmin=isAdmin)
            await message.answer(
                text=f'Добро пожаловать в Административную панель',
                reply_markup=admin_keyboard
            )

        else:
            isAdmin = 'user'
            await state.update_data(isAdmin=isAdmin)
            await message.answer(
                text=f"Добро пожаловать, {employee['name']}!",
                reply_markup=main_keyboard
            )

    else:
        if employee == "employee is not confirmed":
            await message.answer(text="Ожидание подтверждения...")
        else:
            await message.answer(text="Войдите в систему. /start", reply_markup=registration_keyboard)
    if employee:
        await set_chat_id(employee['id'], message.from_user.id)


@dp.callback_query()
async def init_menu(callback_query, state: FSMContext):
    employee = await employee_by_telegram(callback_query.from_user.username)
    logging.info(f'employee: {employee}')
    employee_id = -1
    isAdmin = False
    if employee:
        await state.update_data(employee_id=employee['id'])
        employee_id = employee['id']
        isAdmin = employee['position'] in ['admin', 'marketer']
    await state.update_data(isAdmin=isAdmin)
    logging.info(f'employee_id: {employee_id} isAdmin: {isAdmin}')
    if callback_query.data == "tasks":
        await tasks(callback_query, employee_id)
    elif callback_query.data == "done_tasks":
        await done_tasks(callback_query, employee_id)
    elif callback_query.data == "registration":
        await registration(callback_query, state)
    elif callback_query.data.startswith("get_level_"):
        await process_employee_level(callback_query, state)
    elif callback_query.data.startswith("get_position_"):
        await process_employee_position(callback_query, state)
    elif callback_query.data == "profile":
        await profile(callback_query, employee_id)
    elif callback_query.data == "balance":
        await balance(callback_query, employee_id)
    elif callback_query.data == "get_money":
        await get_money(callback_query, employee_id)
    elif callback_query.data.startswith("view_task_"):
        task_id = int(callback_query.data.split("_")[-1])
        await view_task(callback_query, task_id)
    elif callback_query.data.startswith("finish_task"):
        task_id = int(callback_query.data.split("_")[-1])
        await finish_task(callback_query, task_id, employee_id)
    elif callback_query.data == "add_task":
        await add_task(callback_query, state)
    elif callback_query.data == "all_done_tasks":
        await all_done_tasks(callback_query)
    elif callback_query.data == "all_current_tasks":
        await all_current_tasks(callback_query)
    elif callback_query.data == "balance_manage":
        await balance_manage(callback_query)
    elif callback_query.data == "null_money":
        await null_money(callback_query)
    elif callback_query.data == "online":
        await online(callback_query, employee_id)
    elif callback_query.data == "back":
        await callback_query.message.edit_reply_markup(reply_markup=None)
        if isAdmin:
            await callback_query.message.answer(text="Административная панель", reply_markup=admin_keyboard)
        else:
            await callback_query.message.answer(text="Главное меню", reply_markup=main_keyboard)
    elif callback_query.data == "panel":
        if isAdmin:
            await callback_query.message.answer(text="Административная панель", reply_markup=admin_keyboard)
        else:
            await callback_query.message.answer(text="Главное меню", reply_markup=main_keyboard)


async def registration(callback_query, state: FSMContext):
    await callback_query.message.answer(text="Введите свой ИИН:")
    await state.set_state(RegistrationStates.waiting_for_iin)


async def process_employee_iin(message: Message, state: FSMContext):
    await state.update_data(iin=message.text)
    await message.answer(text='Введите свое имя:')
    await state.set_state(RegistrationStates.waiting_for_name)


async def process_employee_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text='Введите свою фамилию:')
    await state.set_state(RegistrationStates.waiting_for_surname)


async def process_employee_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await message.answer(text='Введите свое отчество:')
    await state.set_state(RegistrationStates.waiting_for_middlename)


async def process_employee_middlename(message: Message, state: FSMContext):
    await state.update_data(middlename=message.text)
    await message.answer(text='Введите свой номер телефона:')
    await state.set_state(RegistrationStates.waiting_for_phone)


async def process_employee_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer(text='Выберите свой уровень:', reply_markup=get_level_keyboard())
    # await state.set_state(RegistrationStates.waiting_for_level)


# @dp.callback_query(F.data.startswith('get_level_'))
async def process_employee_level(callback: CallbackQuery, state: FSMContext):
    employee_level = callback.data.split('_')[2]
    await state.update_data(level=employee_level)
    # await state.update_data(level = callback.message.text)
    await callback.message.answer(text='Выберите свою должность:', reply_markup=get_position_keyboard())
    # await state.set_state(RegistrationStates.waiting_for_position)


# @dp.callback_query(F.data.startswith('get_position_'))
async def process_employee_position(callback: CallbackQuery, state: FSMContext):
    employee_data = await state.get_data()
    iin = employee_data.get('iin')
    name = employee_data.get('name')
    surname = employee_data.get('surname')
    middlename = employee_data.get('middlename')
    phone = employee_data.get('phone')
    employee_position = callback.data.split("_")[2]
    telegram_username = callback.from_user.username
    employee_level = employee_data.get('level')
    await state.update_data(position=employee_position)
    await register_employee(iin, name, middlename, surname, phone, employee_level, employee_position, telegram_username)
    admin_chat_ids = await get_admin_chatid()
    message = f"Зарегистрирован новый пользователь @{telegram_username}. Необходимо подтверждение."
    for id in admin_chat_ids:
        await store_notification(id, message)
        await bot.send_message(chat_id=id, text=message)
    await state.clear()
    await callback.message.answer(text=f'Вы успешно зарегистрировались. - /start')
    # await command_start_handler(callback.message)


async def online(callback_query, employee_id) -> None:
    """
        if i click one it onlne
        after again it false and show Online or Offline
   """
    status = await get_online(employee_id)
    new_status = not status
    await set_online(employee_id, new_status)
    await callback_query.message.answer(text=f"Вы теперь {'Online' if new_status else 'Offline'}")
    # await set_chat_id(employee_id, callback_query.message.from_user.id)


async def profile(event, employee_id) -> None:
    employee = await employee_by_id(employee_id)
    logging.info(f'employee: {employee} {employee_id}')
    response_text = (
        f"Личный кабинет\nИмя: {employee['name']}\nБаланс: {employee['balance']}"
    )
    if isinstance(event, Message):
        await event.answer(text=response_text, reply_markup=profile_keyboard)
    elif isinstance(event, CallbackQuery):
        await event.message.answer(text=response_text, reply_markup=profile_keyboard)


async def tasks(event, employee_id) -> None:
    employee = await employee_by_id(employee_id)
    if not employee:
        await event.answer(text="Доступ запрещен")
        return

    tasks = await current_employee_tasks(employee_id)
    if not tasks:
        response_text = "У вас нет задач"
    else:
        task_messages = []
        for task in tasks:
            task_details = (
                f"Задача: {task['task_name']}\n"
                f"Описание: {task['task_description']}\n"
                f"Файл: {settings.BASE_URL}/{task['task_file']}\n"
                f"Статус: {task['status']}\n"
                f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
                f"Приоритет: {task['priority']}\n"
                f"Рейтинг: {task['rating']}\n"
                f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Завершить задачу", callback_data=f"finish_task_{task['task_id']}")],
                [back_button]
            ])
            task_messages.append((task_details, keyboard))

    if isinstance(event, Message):
        if not tasks:
            await event.answer(text=response_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]]))
        else:
            for task_details, keyboard in task_messages:
                await event.answer(text=task_details, reply_markup=keyboard)
    elif isinstance(event, CallbackQuery):
        if not tasks:
            await event.message.answer(text=response_text,
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]]))
        else:
            for task_details, keyboard in task_messages:
                await event.message.answer(text=task_details, reply_markup=keyboard)


async def all_done_tasks(callback_query) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    all_done_tasks = await done_task_list()
    if not all_done_tasks:
        await callback_query.message.answer(
            text="Нет выполненных задач",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )
    else:
        for task in all_done_tasks:
            task_details = (
                f"Задача: {task['task_name']}\n"
                f"Описание: {task['task_description']}\n"
                f"Статус: {task['status']}\n"
                f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
                f"Приоритет: {task['priority']}\n"
                f"Рейтинг: {task['rating']}\n"
                f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Посмотреть задачу", callback_data=f"view_task_{task['id']}")],
                [back_button]
            ])
            await callback_query.message.answer(text=task_details, reply_markup=keyboard)


async def all_current_tasks(callback_query) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    all_current_tasks = await current_tasks()
    if not all_current_tasks:
        await callback_query.message.answer(
            text="Нет новых задач",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )
    else:
        for task in all_current_tasks:
            task_details = (
                f"Задача: {task['task_name']}\n"
                f"Описание: {task['task_description']}\n"
                f"Статус: {task['status']}\n"
                f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
                f"Приоритет: {task['priority']}\n"
                f"Рейтинг: {task['rating']}\n"
                f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Посмотреть задачу", callback_data=f"view_task_{task['id']}")],
                [back_button]
            ])
            await callback_query.message.answer(text=task_details, reply_markup=keyboard)


async def balance_manage(callback_query) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(
        text="Управление счетами",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    )


async def null_money(callback_query) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(
        text="Обнуление счета",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    )


# @router.callback_query(F.data == "add_task")
async def add_task(callback_query, state: FSMContext):
    # await callback.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(
        text="Введите название задачи:",
    )
    await state.set_state(AddTaskStates.waiting_for_name)


async def process_name_task(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        text=f"Введите описание задачи(необязательно):",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[skip_button]], resize_keyboard=True)
    )
    await state.set_state(AddTaskStates.waiting_for_description)


async def process_description_task(message: Message, state: FSMContext):
    if message.text != 'Пропустить':
        await state.update_data(description=message.text)
    else:
        await state.update_data(description='')
    await message.answer(
        text=f"Прикрепите файл к задаче(необязательно):",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[skip_button]], resize_keyboard=True)
    )
    await state.set_state(AddTaskStates.waiting_for_filePath)


async def process_filePath_task(message: Message, state: FSMContext):
    if message.text != 'Пропустить':
        file_name = None
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
        elif message.photo:
            file_id = message.photo[-1].file_id  # Get the highest resolution photo
            file_name = f"{file_id}.jpg"

        if file_id and file_name:
            file = await bot.get_file(file_id)
            filePath = file.file
            downloaded_file = await bot.download_file(filePath)
            save_path = os.path.join(SAVE_DIR, file_name)

            with open(save_path, 'wb') as f:
                f.write(downloaded_file.getvalue())

            await state.update_data(filePath=file_name)
    else:
        await state.update_data(filePath='')

    await message.answer(
        text=f"Прикрепите ссылку к задаче(необязательно):",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[skip_button]], resize_keyboard=True)
    )
    await state.set_state(AddTaskStates.waiting_for_link)


async def process_link_task(message: Message, state: FSMContext):
    if message.text != 'Пропустить':
        await state.update_data(link=message.text)
    else:
        await state.update_data(link='')

    task_data = await state.get_data()
    name = task_data.get('name')
    description = task_data.get('description')
    file = task_data.get('filePath')
    link = task_data.get('link')
    await task_create(name, description, file, link)
    await state.clear()
    await message.answer(
        text="Вы успешно добавили задачу.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    )


async def done_tasks(callback_query, employee_id) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    tasks = await done_employee_tasks(employee_id)
    if not tasks:
        await callback_query.message.answer(
            text="У вас нет выполненных задач",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )
    else:
        for task in tasks:
            task_details = (
                f"Задача: {task['task_name']}\n"
                f"Описание: {task['task_description']}\n"
                f"Статус: {task['status']}\n"
                f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
                f"Приоритет: {task['priority']}\n"
                f"Рейтинг: {task['rating']}\n"
                f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
            await callback_query.message.answer(text=task_details, reply_markup=keyboard)


async def balance(callback_query, employee_id) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    balance = await show_balance(employee_id)
    if not balance:
        await callback_query.message.answer(
            text="У вас еще нет баланса",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )
    else:
        await callback_query.message.answer(
            text=f"Ваш баланс {balance}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )


async def get_money(callback_query, employee_id) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    employee = await employee_by_id(employee_id)
    output_msg = await balance_output(employee_id)
    message = f"Пользователь {employee['name']} {employee['surname']} запросил вывод средств {employee['balance']}. Необходимо подтверждение.\n "
    message += f"Чтобы подтвердить вывод средств, перейдите в административную панель"
    await notify_marketer(message)
    await callback_query.message.answer(
        text=output_msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    )


async def finish_task(callback_query, task_id, employee_id):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    finish_task = await submit_task_func(employee_id, task_id)
    if not finish_task:
        await callback_query.message.answer(
            text="Задача не найдена",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )
    logging.info(f'finish_task: {finish_task}')
    await callback_query.message.answer(
        text=f"Вы успешно завершили задачу",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    )
    ## notify marketer
    employee = Employee.objects.get(id=employee_id)
    await notify_marketer(
        f"Сотрудники {employee.name} {employee.surname} закончил задачу: {finish_task.id} - {finish_task.task.name}")


async def view_task(callback_query, task_id):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    task = await get_task_by_id(task_id)
    if not task:
        await callback_query.message.answer(
            text="Задача не найдена",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )
    else:
        task_details = (
            f"Задача ID: {task['id']}\n"
            f"Статус: {task['status']}\n"
            f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
            f"Приоритет: {task['priority']}\n"
            f"Рейтинг: {task['rating']}\n"
            f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            f"Создано: {format_datetime(task['created_at'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
            f"Обновлено: {format_datetime(task['updated_at'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
        )
        await callback_query.message.answer(
            text=task_details,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        )


async def get_task_by_id(task_id):
    tasks = await current_employee_tasks(employee_id)
    for task in tasks:
        if task['id'] == task_id:
            return task
    return None


dp.message.register(process_employee_iin, RegistrationStates.waiting_for_iin)
dp.message.register(process_employee_name, RegistrationStates.waiting_for_name)
dp.message.register(process_employee_surname, RegistrationStates.waiting_for_surname)
dp.message.register(process_employee_middlename, RegistrationStates.waiting_for_middlename)
dp.message.register(process_employee_phone, RegistrationStates.waiting_for_phone)

dp.message.register(process_name_task, AddTaskStates.waiting_for_name)
dp.message.register(process_description_task, AddTaskStates.waiting_for_description)
dp.message.register(process_filePath_task, AddTaskStates.waiting_for_filePath)
dp.message.register(process_link_task, AddTaskStates.waiting_for_link)


async def start_bot():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
