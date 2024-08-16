# signals.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EmployeeTask, Employee
from aiogram import Bot

load_dotenv()

API_TOKEN = os.getenv('TOKEN')

bot = Bot(token=API_TOKEN)


@receiver(post_save, sender=EmployeeTask)
async def send_employee_task_notification(sender, instance, created, **kwargs):
    if created:
        ## check if position then skip
        if instance.employee is None:
            return
        employee = instance.employee
        chat_id = employee.chat_id
        message_employee = "У вас появилась новая задача: {}".format(instance.task.name)
        message_admin_marketer = f"Новая задача для {employee.position}: {instance.task.name}"
        logging.info(f"New task for {employee.fio} (chat_id {chat_id}): {instance.task.name}")
        try:
            await bot.send_message(chat_id=chat_id, text=message_employee)
        except Exception as e:
            print(f"Error sending message to employee {employee.fio} (chat_id {chat_id}): {e}")

        if employee.position in ['admin', 'marketer']:
            try:
                await bot.send_message(chat_id=chat_id, text=message_admin_marketer)
            except Exception as e:
                print(f"Error sending admin/marketer message to chat_id {chat_id}: {e}")
