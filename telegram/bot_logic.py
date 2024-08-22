import asyncio
import logging
import os
from .views import *
from .models import POSITION_CHOICES, STATUS_CHOICES
from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher, html, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, BotCommand, BotCommandScopeChat
from babel.dates import format_datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.conf import settings
import re

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
    [InlineKeyboardButton(text="Старт/Стоп", callback_data="online")],
    [InlineKeyboardButton(text="Текущие задачи", callback_data="tasks")],
    [InlineKeyboardButton(text="Личный кабинет", callback_data="profile")],
    # [InlineKeyboardButton(text="Чат с маркетологом", callback_data="chat")],
])

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить новую задачу", callback_data="add_task")],
    [InlineKeyboardButton(text="Текущие задачи", callback_data="all_current_tasks")],
    [InlineKeyboardButton(text="Выполненные задачи", callback_data="all_done_tasks")],
])

profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Выполненные задачи", callback_data="done_tasks")],
    [InlineKeyboardButton(text="Запросить вывод средств", callback_data="get_money")],
])

back_button = InlineKeyboardButton(text="Назад", callback_data="back")
panel_button = InlineKeyboardButton(text="Панель", callback_data="panel")
skip_button = KeyboardButton(text="Пропустить", callback_data="skip")


async def set_commands():
    pass
    # commands = [
    #     BotCommand(command="start", description="Start the bot"),
    #     BotCommand(command="help", description="Show help"),
    #     BotCommand(command="balance", description="Show balance"),
    #     BotCommand(command="get_money", description="Get money"),
    #     BotCommand(command="tasks", description="Show tasks"),
    #     BotCommand(command="done_tasks", description="Show done tasks"),
    #     BotCommand(command="online", description="Show online status"),
    #     BotCommand(command="profile", description="Show profile"),
    #     BotCommand(command="chat", description="Chat with marketer"),
    #     BotCommand(command="employees_list", description="List of employees"),
    # ]
    # await bot.set_my_commands(commands, scope=BotCommandScopeChat())


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


def main_kb(typeUser, params=None):
    if typeUser == 'guest':
        kb_list = [
            [KeyboardButton(text="/start")],
            [KeyboardButton(text="Регистрация")],
        ]
    elif typeUser == 'user':
        kb_list = [
            [KeyboardButton(text="/start")],
            [KeyboardButton(text="Онлайн/Оффлайн")],
            [KeyboardButton(text="Текущие задачи"),
             KeyboardButton(text="Личный кабинет")],
        ]
    elif typeUser in ['admin', 'marketer']:
        kb_list = [
            [KeyboardButton(text="/start")],
            [KeyboardButton(text="Текущие задачи сотрудника")],
            [KeyboardButton(text="Выполненные задачи сотрудника")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        is_personal=True,
        input_field_placeholder='Выберите действие'
    )


class InitStates(StatesGroup):
    user_id = State()
    employee_id = State()
    isAdmin = State()
    employee_position = State()
    employee_level = State()
    isOnline = State()
    employee = State()


class AddTaskStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_filePath = State()
    waiting_for_link = State()
    waiting_for_date = State()  # set deadline
    waiting_for_comments = State()  # feedback


class RegistrationStates(StatesGroup):
    waiting_for_iin = State()
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_middlename = State()
    waiting_for_phone = State()
    waiting_for_level = State()
    waiting_for_position = State()


@dp.message(Command('start'))
async def command_start_handler(message: Message, state: FSMContext):
    logging.info(f'message: {message}')
    user_id = message.from_user.id
    employee = await employee_by_telegram(user_id)
    logging.info(f'employee: {employee} {user_id}')
    logging.info(f'user_id {user_id}')

    try:
        if employee is not None:
            await set_chat_id(employee['id'], message.from_user.id)
            await state.update_data(employee=employee)
            if not employee['is_confirmed']:
                await message.answer(text="Ожидание подтверждения...")
                return
            await state.update_data(employee_id=employee['id'])
            if employee['position'] == 'admin' or employee['position'] == 'marketer':
                isAdmin = employee['position'] in ['admin', 'marketer']
                await state.update_data(isAdmin=isAdmin)
                await bot.send_message(chat_id=message.from_user.id, text="Добро пожаловать в систему")
                await message.answer(
                    text=f'Добро пожаловать в Административную панель',
                    reply_markup=main_kb(typeUser='admin')
                )
            else:
                isAdmin = 'user'
                logging.info(f'init user: {employee["telegram"]}')
                await bot.send_message(chat_id=message.from_user.id, text="Добро пожаловать в систему")
                await state.update_data(isAdmin=isAdmin)

                await message.answer(
                    text=f"Добро пожаловать, {employee['name']}!",
                    reply_markup=main_kb(typeUser='user'))
        else:
            await message.answer(
                text=f"Добро пожаловать!",
                reply_markup=main_kb(typeUser='guest')
            )
    except Exception as e:
        logging.error(f'error: {e}')
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")
        return


#### admin ####

@dp.message(F.text.lower() == "выполненные задачи сотрудника")  # "tasks" -> "задачи"
@dp.message(Command('done_tasks_users'))
async def handle_tasks(message: types.Message, state: FSMContext):
    await admin_done_tasks(message, state)


@dp.message(F.text.lower() == "текущие задачи сотрудника")  # "all_current_tasks" -> "все текущие задачи"
@dp.message(Command('current_tasks_users'))
async def handle_all_current_tasks(message: types.Message, state: FSMContext):
    await admin_all_current_tasks(message)


##################
### misc ####


##################
#### registration ####
@dp.message(F.text.lower() == "регистрация")  # "registration" -> "регистрация"
@dp.message(Command('registration'))
async def handle_registration(message: types.Message, state: FSMContext):
    await registration(message, state)


#######################
@dp.message(F.text.lower() == 'онлайн/оффлайн')
async def start_stop(message: Message, state: FSMContext):
    await message.answer(text="Выберите статус", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Online", callback_data="online")],
        [InlineKeyboardButton(text="Offline", callback_data="offline")],
    ]))


@dp.message(F.text.lower() == "текущие задачи")  # "tasks" -> "задачи"
@dp.message(Command('tasks'))
async def handle_tasks(message: types.Message, state: FSMContext):
    await tasks(message, state)


#### личный кабинет ####
@dp.message(F.text.lower() == "личный кабинет")  # "profile" -> "профиль"
@dp.message(Command('profile'))
async def handle_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    logging.info(f'data: {data}')
    await profile(message, data.get('employee_id'))


@dp.callback_query(F.data.startswith("view_task_"))
async def handle_view_task(callback_query: CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split("_")[-1])
    await view_task(callback_query, task_id)


#################
async def registration(message, state: FSMContext):
    await message.answer(text="Введите свой ИИН:")
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
    # await state.set_state(RegistrationStates.waiting_for_level)
    await message.answer(text='Выберите свою должность:', reply_markup=get_position_keyboard())


@dp.callback_query(F.data.startswith('get_position_'))
async def process_employee_position(callback: CallbackQuery, state: FSMContext):
    employee_data = await state.get_data()
    iin = employee_data.get('iin')
    name = employee_data.get('name')
    surname = employee_data.get('surname')
    middlename = employee_data.get('middlename')
    phone = employee_data.get('phone')
    employee_position = callback.data.split("_")[2]
    telegram_id = callback.from_user.id
    employee_level = 'junior'
    await state.update_data(position=employee_position)
    user = await register_employee(iin, name, middlename, surname, phone, employee_level, employee_position,
                                   telegram_id)
    admin_chat_ids = await get_admin_chatid()
    message = f"Зарегистрирован новый пользователь @{telegram_id}. Необходимо подтверждение."
    ## todos: notify admin and after admin confirm notify user
    for id in admin_chat_ids:
        await store_notification(id, message)
        await bot.send_message(chat_id=id, text=message)
    await state.clear()
    await callback.message.answer(
        text=f"user {name} {surname} отправлен на подтверждение, когда он будет подтвержден, вы можете начать работу")


@dp.callback_query(F.data == "online")
async def online(callback_query, state: FSMContext) -> None:
    """
        if i click one it onlne
        after again it false and show Online or Offline
   """
    data = await state.get_data()
    employee_id = data.get('employee_id')
    status = True
    await set_status(employee_id, status)
    await callback_query.message.answer(text=f"Вы теперь {'Online' if status else 'Offline'}")
    # await set_chat_id(employee_id, callback_query.message.from_user.id)


@dp.callback_query(F.data == "offline")
async def offline(callback_query, state: FSMContext) -> None:
    """
        if i click one it onlne
        after again it false and show Online or Offline
   """
    data = await state.get_data()
    employee_id = data.get('employee_id')
    status = False
    await set_status(employee_id, status)
    await callback_query.message.answer(text=f"Вы теперь {'Online' if status else 'Offline'}")
    # await set_chat_id(employee_id, callback_query.message.from_user.id)


async def profile(event, employee_id) -> None:
    logging.info(f'profile employee_id: {employee_id}')
    employee = await employee_by_id(employee_id)
    logging.info(f'employee: {employee} {employee_id}')
    response_text = (
        f"Личный кабинет\nИмя: {employee['name']}\nБаланс: {employee['balance']}"
    )
    if isinstance(event, Message):
        await event.answer(text=response_text, reply_markup=profile_keyboard)
    elif isinstance(event, CallbackQuery):
        await event.message.answer(text=response_text, reply_markup=profile_keyboard)


async def tasks(event, state) -> None:
    data = await state.get_data()
    employee_id = data.get('employee_id')
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
            inline_keyboard = [
                [InlineKeyboardButton(text="Завершить задачу", callback_data=f"finish_task_{task['task_id']}")],
                [InlineKeyboardButton(text="Изменить статус", callback_data=f"set_status_task_{task['task_id']}")],
                [InlineKeyboardButton(text="Добавить комментарий", callback_data=f"comments_task_{task['task_id']}")],

            ]
            ## if employeee is mobilographer then add set date button
            if employee['position'] == 'mobilograph':
                inline_keyboard.append(
                    [InlineKeyboardButton(text="Установить дату", callback_data=f"set_date_task_{task['task_id']}")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
            task_messages.append((task_details, keyboard))

    if isinstance(event, Message):
        if not tasks:
            await event.answer(text=response_text)
        else:
            for task_details, keyboard in task_messages:
                await event.answer(text=task_details, reply_markup=keyboard, parse_mode='HTML')
    elif isinstance(event, CallbackQuery):
        if not tasks:
            pass
        else:
            for task_details, keyboard in task_messages:
                await event.message.answer(text=task_details, reply_markup=keyboard, mode=ParseMode.HTML)


async def admin_done_tasks(message, state: FSMContext) -> None:
    logging.info(f'admin all_done_tasks')
    all_done_tasks = await done_task_list()
    if not all_done_tasks:
        await message.answer(
            text="Нет выполненных задач",
        )
    else:
        for task in all_done_tasks:
            logging.info(f'all_done_tasks: {all_done_tasks}')
            employee = await employee_by_id(task['employee_id'])
            fio = f"{employee['name']} {employee['middle_name']} {employee['surname']}"
            task_details = (
                f"Задача: {task['task_name']}\n"
                f"Сотрудник: {fio}\n"
                f"Описание: {task['task_description']}\n"
                f"Статус: {task['status']}\n"
                f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
                f"Приоритет: {task['priority']}\n"
                f"Рейтинг: {task['rating']}\n"
                f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            )
            await message.answer(text=task_details)


async def admin_all_current_tasks(message) -> None:
    logging.info(f'admin all_current_tasks')
    all_current_tasks = await current_tasks()
    if not all_current_tasks:
        await message.answer(
            text="Нет новых задач",

        )
    else:
        logging.info(f'all_current_tasks: {all_current_tasks}')
        for task in all_current_tasks:
            employee = await employee_by_id(task['employee_id'])
            fio = f"{employee['name']} {employee['middle_name']} {employee['surname']}"
            task_details = (
                f"Задача: {task['task_name']}\n"
                f"Сотрудник: {fio}\n"
                f"Описание: {task['task_description']}\n"
                f"Статус: {task['status']}\n"
                f"Срок: {format_datetime(task['deadline'], 'd MMMM yyyy, H:mm', locale='ru_RU')}\n"
                f"Приоритет: {task['priority']}\n"
                f"Рейтинг: {task['rating']}\n"
                f"Проверено: {'Да' if task['checked'] else 'Нет'}\n"
            )
            await message.answer(text=task_details)


async def balance_manage(callback_query) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(
        text="Управление счетами",

    )


async def null_money(callback_query) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(
        text="Обнуление счета",

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
    )


@dp.callback_query(F.data == "done_tasks")
async def done_tasks(callback_query, state: FSMContext) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    employee_id = data.get('employee_id')
    tasks = await done_employee_tasks(employee_id)
    if not tasks:
        await callback_query.message.answer(
            text="У вас нет выполненных задач"
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

            await callback_query.message.answer(text=task_details)


async def balance(callback_query, employee_id) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    balance = await show_balance(employee_id)
    if not balance:
        await callback_query.message.answer(
            text="У вас еще нет баланса",

        )
    else:
        await callback_query.message.answer(
            text=f"Ваш баланс {balance}"
        )


@dp.callback_query(F.data == "get_money")
async def get_money(callback_query, state: FSMContext) -> None:
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    employee_id = data.get('employee_id')
    employee = await employee_by_id(employee_id)
    output_msg = await balance_output(employee_id)
    message = f"Пользователь {employee['name']} {employee['surname']} запросил вывод средств {employee['balance']}. Необходимо подтверждение.\n "
    message += f"Чтобы подтвердить вывод средств, перейдите в административную панель"
    await notify_marketer(message)
    await callback_query.message.answer(
        text=output_msg,

    )


@dp.callback_query(F.data.startswith("finish_task_"))
async def finish_task(callback_query, state: FSMContext) -> None:
    data = await state.get_data()
    employee_id = data.get('employee_id')
    logging.info(f'finish_task: {employee_id}')
    task_id = int(callback_query.data.split("_")[-1])
    logging.info(f'task_id: {task_id}')
    await callback_query.message.edit_reply_markup(reply_markup=None)
    finish_task = await submit_task_func(employee_id, task_id)
    if not finish_task:
        await callback_query.message.answer(
            text="Задача не найдена",

        )
    logging.info(f'finish_task: {finish_task}')
    await callback_query.message.answer(
        text=f"Вы успешно завершили задачу",

    )
    # ## notify marketer
    employee = Employee.objects.get(id=employee_id)
    await notify_marketer(
        f"Сотрудники {employee.name} {employee.surname} закончил задачу: {finish_task.id} - {finish_task.task.name}")


@dp.callback_query(F.data.startswith("set_date_task_"))
async def set_date_task_(callback_query, state: FSMContext) -> None:
    await callback_query.message.answer('Введите дату и время в формате: 13-12-2021/23:59')
    ## get message and check date while is correct
    await state.set_state(AddTaskStates.waiting_for_date)
    task_id = int(callback_query.data.split("_")[-1])
    await state.update_data(task_id=task_id)


@dp.callback_query(F.data.startswith("set_status_task_"))
async def set_status_task_(callback_query, state: FSMContext) -> None:
    await callback_query.message.answer('Выберите статус задачи')
    task_id = int(callback_query.data.split("_")[-1])

    await callback_query.message.answer(text="Выберите статус задачи",
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text=STATUS_CHOICES[1][1],
                                                                  callback_data=f"status_task_inwork_{task_id}")],
                                            [InlineKeyboardButton(text=STATUS_CHOICES[2][1],
                                                                  callback_data=f"status_task_done_{task_id}")],
                                            [InlineKeyboardButton(text=STATUS_CHOICES[4][1],
                                                                  callback_data=f"status_task_cancel_{task_id}")],
                                        ]))


@dp.callback_query(F.data.startswith("status_task_"))
async def status_task_(callback_query, state: FSMContext) -> None:
    status = callback_query.data.split("_")
    task_id = status[len(status) - 1]
    status_task = status[len(status) - 2]
    if status_task == 'inwork':
        status_task = STATUS_CHOICES[1][0]
    elif status_task == 'done':
        status_task = STATUS_CHOICES[2][0]
    elif status_task == 'cancel':
        status_task = STATUS_CHOICES[4][0]
    logging.info(f'status: {status}')
    data = await state.get_data()
    employee_id = data.get('employee_id')
    await submit_task_status_func(status_task, employee_id, task_id)
    await callback_query.message.answer(f'Статус задачи изменен на "{status_task}"')
    return


@dp.callback_query(F.data.startswith("comments_task_"))
async def comments_task_(callback_query, state: FSMContext) -> None:
    await callback_query.message.answer('Введите комментарий к задаче')
    await callback_query.message.answer(
        'Если комментарий начинается с слов "завершить" или "закрыть", то задача будет завершена')
    ## get message and check date while is correct
    await state.set_state(AddTaskStates.waiting_for_comments)
    task_id = int(callback_query.data.split("_")[-1])
    await state.update_data(task_id=task_id)


async def process_date_task(message: Message, state: FSMContext):
    date = message.text
    data = await state.get_data()
    employee_id = data.get('employee_id')
    task_id = data.get('task_id')
    patern = re.compile(r'\d{2}-\d{2}-\d{4}/\d{2}:\d{2}')
    if not patern.match(date):
        await message.answer('Неверный формат даты')
        return
    await state.update_data(date=date)
    await message.answer('Дата установлена')
    task_data = await state.get_data()
    date = task_data.get('date')
    logging.info(f'date: {date}')
    await submit_task_deadline_func(date, employee_id, task_id)


async def process_comments_task(message: Message, state: FSMContext):
    comment = message.text
    if not comment:
        await message.answer('Комментарий не может быть пустым')
        return
    data = await state.get_data()

    # clear comments from vulnerabilities
    comment = re.sub(r'[^\w\s]', '', comment)
    comment = re.sub(r'\s+', ' ', comment)
    # sql injection
    comment = re.sub(r'--', '', comment)
    comments = data.get('comments', [])
    comments.append(comment)
    await state.update_data(comments=comments)
    if comment.startswith('завершить') or comment.startswith('закрыть'):
        employee_id = data.get('employee_id')
        task_id = data.get('task_id')
        full_comment = ' '.join(comments)
        # clear words close and finish
        full_comment = re.sub(r'закрыть', '', full_comment)
        full_comment = re.sub(r'завершить', '', full_comment)
        await submit_task_comment_func(full_comment, employee_id, task_id)
        await state.update_data(comments=[])

        await message.answer('Комментарий добавлен')
        return


async def view_task(callback_query, task_id):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    task = await get_task_by_id(task_id)
    if not task:
        await callback_query.message.answer(
            text="Задача не найдена",

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

        )


async def get_task_by_id(task_id):
    tasks = await current_employee_tasks(employee_id)
    for task in tasks:
        if task['id'] == task_id:
            return task
    return None


users = {}

dp.message.register(process_employee_iin, RegistrationStates.waiting_for_iin)
dp.message.register(process_employee_name, RegistrationStates.waiting_for_name)
dp.message.register(process_employee_surname, RegistrationStates.waiting_for_surname)
dp.message.register(process_employee_middlename, RegistrationStates.waiting_for_middlename)
dp.message.register(process_employee_phone, RegistrationStates.waiting_for_phone)

dp.message.register(process_name_task, AddTaskStates.waiting_for_name)
dp.message.register(process_description_task, AddTaskStates.waiting_for_description)
dp.message.register(process_filePath_task, AddTaskStates.waiting_for_filePath)
dp.message.register(process_link_task, AddTaskStates.waiting_for_link)
dp.message.register(process_date_task, AddTaskStates.waiting_for_date)
dp.message.register(process_comments_task, AddTaskStates.waiting_for_comments)


async def start_bot():
    await dp.start_polling(bot)
    # await set_commands()


if __name__ == "__main__":
    asyncio.run(start_bot())
