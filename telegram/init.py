def main_kb(isAdmin):
    kb_list = [
        [KeyboardButton(text="Онлайн/Оффлайн")],
        [KeyboardButton(text="Текущие задачи"),
         KeyboardButton(text="Личный кабинет")],
    ]
    if isAdmin in ['admin', 'marketer']:
        kb_list = [
            [
             KeyboardButton(text="Добавить новую задачу")],
            [KeyboardButton(text="Текущие задачи")],
            [KeyboardButton(text="Выполненные задачи")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        is_personal=True,
        input_field_placeholder='Выберите действие'
    )

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
    # [InlineKeyboardButton(text="Управление счетами", callback_data="balance_manage")],
    # [InlineKeyboardButton(text="Обнулить счет сотрудника", callback_data="null_money")],
    # [InlineKeyboardButton(text="Чат с сотрудниками", callback_data="employees_list")],
])
profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Выполненные задачи", callback_data="done_tasks")],
    [InlineKeyboardButton(text="Запросить вывод средств", callback_data="get_money")],
])

back_button = InlineKeyboardButton(text="Назад", callback_data="back")
panel_button = InlineKeyboardButton(text="Панель", callback_data="panel")
skip_button = KeyboardButton(text="Пропустить", callback_data="skip")


async def init():
    employee = await employee_by_telegram(callback_query.from_user.id)
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
    elif callback_query.data == "chat":
        await chat(callback_query, employee_id)
    elif callback_query.data == "employees_list":
        await employees_list(callback_query)