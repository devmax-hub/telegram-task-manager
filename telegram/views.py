import logging

from .models import Employee, Task, EmployeeTask, Balance, WithdrawDeposit, TaskHistory, Notification
import os
from asgiref.sync import sync_to_async

from django.db.models import Q
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_TOKEN = os.getenv('TOKEN') 

bot = Bot(token=API_TOKEN)

@sync_to_async
def check_if_banned(telegram):
    employee = Employee.objects.get(telegram=telegram)


@sync_to_async
def task_list():
    task = Task.objects.all().values()
    return list(task)

@sync_to_async
def done_task_list():
    try:
        employee_tasks = EmployeeTask.objects.filter(
            status='завершено',
        ).select_related('task').annotate(
            task_name=F('task__name'),
            task_description=F('task__description'),
            task_file_path=F('task__file_path'),
            task_link=F('task__link'),
        ).values(
            'id', 'employee_id', 'task_id', 'task_name', 'task_description',
            'task_file_path', 'task_link', 'created_at', 'updated_at', 'status',
            'deadline', 'priority', 'checked', 'rating'
        )
    except (EmployeeTask.DoesNotExist):
        return False
    return list(employee_tasks)

@sync_to_async
def register_employee(iin, name, middlename, surname, phone, employee_level, employee_position, telegram_username):
    try:
        employee = Employee.objects.get(iin=iin)
        data = {}
        data['error'] = 'Employee already exists'
        return data
    except Employee.DoesNotExist:
        employee = Employee.objects.create(
            iin=iin,
            name=name,
            middle_name=middlename,
            surname=surname,
            phone=phone,
            level=employee_level,
            position=employee_position,
            telegram=telegram_username
        )
        data = {
            'id': employee.id,
            'iin': employee.iin,
            'name': employee.name,
            'middle_name': employee.middle_name,
            'surname': employee.surname,
            'phone': employee.phone,
            'level': employee.level,
            'position': employee.position,
            'telegram': employee.telegram
        }
        return data

@sync_to_async
def current_tasks():
    try:
        employee_tasks = EmployeeTask.objects.filter(
            Q(status='в процессе') | Q(status='новое'),
        ).select_related('task').annotate(
            task_name=F('task__name'),
            task_description=F('task__description'),
            task_file_path=F('task__file_path'),
            task_link=F('task__link'),
        ).values(
            'id', 'employee_id', 'task_id', 'task_name', 'task_description',
            'task_file_path', 'task_link', 'created_at', 'updated_at', 'status',
            'deadline', 'priority', 'checked', 'rating'
        )
    except (EmployeeTask.DoesNotExist):
        return False

    return list(employee_tasks)


@sync_to_async
def task_detail(id):
    task = Task.objects.filter(id=id).values()[0]
    return task

@sync_to_async
def task_create(name, description, file, link):
    task = Task.objects.create(
        name = name,
        description = description,
        file = file,
        link = link
    )
    return True

@sync_to_async
def task_delete(id):
    task = Task.objects.get(id=id).delete()
    return 'deleted'

@sync_to_async
def task_update(id, name, description, file, link):
    task = Task.objects.filter(id=id).update(
        name = name,
        description = description,
        file = file,
        link = link
    )
    
    task.save()

    return list(task)

from django.db.models import Count, Q
from asgiref.sync import sync_to_async



@sync_to_async
def submit_task_func(employee_id, task_id):
    logging.info(f'Employee task {employee_id} submitted task {task_id}')
    employee_task = EmployeeTask.objects.get(employee_id = employee_id, task_id = task_id)
    employee_task.status="завершено"
    employee_task.save()
    return employee_task


# def finish_task_func(employee_id, task_id):
#     try:
#         current_employee = Employee.objects.get(id=employee_id)

#         next_position = "admin"
        
#         if current_employee.position == "copywriter":
#             next_position = "mobilograph"
#         elif current_employee.position == "mobilograph":
#             next_position = "editor"
#         elif current_employee.position == "editor":
#             next_position = "designer"
#         elif current_employee.position == "designer":
#             next_position = "smm"
#         elif current_employee.position == "smm":
#             EmployeeTask.objects.filter(
#                 task_id=task_id
#             ).update(
#                 status="завершено"
#             )

#             return True

        
#         next_employee = (
#             Employee.objects.filter(position=next_position)
#             .annotate(task_count=Count('employeetask'))
#             .order_by('-rating', 'task_count')
#             .first()
#         )

#         if next_employee:

#             # EmployeeTask.objects.filter(
#             #     employee_id = employee_id,
#             #     task_id = task_id
#             # ).update(
#             #     status="завершено"
#             # ) 

#             # print(task_id)

#             employee_tasks = EmployeeTask.objects.filter(
#                 task_id=task_id,
#                 employee_id=employee_id
#             ).first()

#             EmployeeTask.objects.create(
#                 employee_id = next_employee.id, 
#                 task_id = employee_tasks.task_id, 
#                 status = "новое",
#                 deadline = employee_tasks.deadline,
#                 priority = employee_tasks.priority,
#                 checked = False,
#                 rating = employee_tasks.rating
#             )

#             TaskHistory.objects.create(
#                 employee=current_employee,
#                 task=employee_tasks.task,
#             )

#             message = "У вас новая задача"
#             bot.send_message(chat_id=next_employee.chat_id, message=message)
#             Notification.objects.create(
#                 employee=next_employee,
#                 task=employee_tasks.task
#             )

#             return True
#         else:
#             return False
        
#     except Employee.DoesNotExist:
#         return False

@sync_to_async
def employee_by_telegram(telegram):
    try:
        employee = Employee.objects.get(telegram=telegram)
        if employee.is_confirmed:
            return {
                "id": employee.pk,
                "surname": employee.surname,
                "name": employee.name,
                "middle_name": employee.middle_name,
                "telegram": employee.telegram,
                "position": employee.position,
            }
        else:
            return "employee is not confirmed"
    except (Employee.DoesNotExist):
        return False        

@sync_to_async
def employee_by_id(employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
        
        try:
            balance = Balance.objects.get(employee_id=employee_id)
            balance = balance.balance
        except ObjectDoesNotExist:
            balance = 0

        return {
            "id": employee.id,
            "surname": employee.surname,
            "name": employee.name,
            "middle_name": employee.middle_name,
            "telegram": employee.telegram,
            "position": employee.position,
            "balance": balance,
        }
    except (Employee.DoesNotExist):
        return False

@sync_to_async
def current_employee_tasks(employee_id):
    employee = Employee.objects.get(id=employee_id)
    try:
        employee_tasks = EmployeeTask.objects.filter(
            Q(status='в процессе') | Q(status='новое'),
            employee=employee
        ).select_related('task').annotate(
            task_name=F('task__name'),
            task_description=F('task__description'),
            task_file=F('task__file'),
            task_link=F('task__link'),
        ).values(
            'id', 'employee_id', 'task_id', 'task_name', 'task_description',
            'task_file', 'task_link', 'created_at', 'updated_at', 'status',
            'deadline', 'priority', 'checked', 'rating'
        )
    except (EmployeeTask.DoesNotExist):
        return False

    return list(employee_tasks)
    # return list(tasks)

@sync_to_async
def done_employee_tasks(employee_id):
    employee = Employee.objects.get(id=employee_id)    
    try:
        employee_tasks = EmployeeTask.objects.filter(
            status='завершено',
            employee=employee
        ).select_related('task').annotate(
            task_name=F('task__name'),
            task_description=F('task__description'),
            task_file_path=F('task__file'),
            task_link=F('task__link'),
        ).values(
            'id', 'employee_id', 'task_id', 'task_name', 'task_description',
            'task_file_path', 'task_link', 'created_at', 'updated_at', 'status',
            'deadline', 'priority', 'checked', 'rating'
        )
    except (EmployeeTask.DoesNotExist):
        return False
    return list(employee_tasks)

@sync_to_async
def employee_tasks(employee_id):
    employee = Employee.objects.get(id=employee_id)    
    try:
        tasks = EmployeeTask.objects.filter(employee=employee).values()
    except (EmployeeTask.DoesNotExist):
        return False
    return list(tasks)

@sync_to_async
def transaction(employee_id, type, amount):
    employee = Employee.objects.get(id = employee_id)
    try:
        balance = Balance.objects.get(employee = employee)
    except ObjectDoesNotExist:
        Balance.objects.create(
            employee = employee,
            balance = 0,
        )
        balance = Balance.objects.get(employee = employee)

    withdraw_deposit = WithdrawDeposit.objects.create(
        balance = balance,
        amount = amount,
        status = 'новое',
        type = type
    )

    if type == 'deposit':
        balance.balance += withdraw_deposit.amount
    else:
        if withdraw_deposit.amount > balance.balance:
            return 'Недостаточно средств'
        else:

            balance.balance -= withdraw_deposit.amount
    return balance.balance

@sync_to_async
def show_balance(employee_id):
    try:
        balance = Balance.objects.get(employee_id=employee_id)
    except ObjectDoesNotExist:
        return False
    return list(balance) 

@sync_to_async
def balance_output(employee_id):
    balance = Balance.objects.get(employee=employee_id)
    if balance.is_approved:
        return f'Средства успешно выведены {balance.balance} тенге.'
    else:
        return 'Зайдите в личный кабинет позже, пока запрос на вывод средств находится на рассмотрении.'


@sync_to_async
def set_chat_id(employee_id, chat_id):
    logging.info(f'Employee {employee_id} chat_id is {chat_id}')
    employee = Employee.objects.get(id=employee_id)
    if employee.chat_id is None:
        employee.chat_id = chat_id
        employee.save()
    
    return True

@sync_to_async
def get_admin_chatid():
    employees = Employee.objects.filter(position='admin')
    id_list = []
    for employee in employees:
        id_list.append(employee.chat_id)

    return id_list

@sync_to_async
def get_marketer_chatid():
    employees = Employee.objects.filter(position='marketer')
    id_list = []
    for employee in employees:
        id_list.append(employee.chat_id)

    return id_list

@sync_to_async
def store_notification(chat_id, message):
    employee = Employee.objects.get(chat_id=chat_id)
    Notification.objects.create(
        employee=employee,
        message=message,
    )


@sync_to_async
def set_online(employee_id, status):
    employee = Employee.objects.get(id=employee_id)
    logging.info(f'Employee {employee_id} is now {"online" if status else "offline"}')
    employee.status = status
    employee.save()
    return status


    return status


@sync_to_async
def get_online(employee_id):
    employee = Employee.objects.get(id=employee_id)
    return employee.status


@sync_to_async
def get_chat_id(employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
        return employee.chat_id
    except Employee.DoesNotExist:
        return None