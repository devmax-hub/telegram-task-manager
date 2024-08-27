# signals.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import EmployeeTask, Employee
from aiogram import Bot
from .tasks import send_messages_to_user
from django_q.tasks import async_task
load_dotenv()

API_TOKEN = os.getenv('TOKEN')

bot = Bot(token=API_TOKEN)


# @receiver(post_save, sender=EmployeeTask)
# async def send_employee_task_notification(sender, instance, created, **kwargs):
#     if created:
#         ## check if position then skip
#         if instance.employee is None:
#             return
#         employee = instance.employee
#         chat_id = employee.chat_id
#         message_employee = "У вас появилась новая задача: {}".format(instance.task.name)
#         message_admin_marketer = f"Новая задача для {employee.position}: {instance.task.name}"
#         logging.info(f"New task for {employee.fio} (chat_id {chat_id}): {instance.task.name}")
#
#         await bot.send_message(chat_id=chat_id, text=message_employee)
#         if employee.position in ['admin', 'marketer']:
#            await bot.send_message(chat_id=chat_id, text=message_admin_marketer)

@receiver(pre_save, sender=EmployeeTask)
def set_autopass(sender, instance, **kwargs):
    """set self.autopass = True"""
    if instance.autopass:
        instance.autopass = True


@receiver(post_save, sender=EmployeeTask)
def sender_notification_handler(sender, instance, **kwargs):
    try:
        """send message to employee"""
        if instance.employee is None:
            return
        logging.info(f"New task for {instance.employee}")
        employee = instance.employee
        chat_id = employee.chat_id
        message_employee = "У вас по задаче: {}".format(instance.task.name)
        async_task('telegram.tasks.send_message_to_user_sync', chat_id=chat_id, message=message_employee)
        for m in Employee.objects.filter(position='marketer').all():
            chat_id = m.chat_id
            message_marketer = f"Новая задача для {m.position} - {m.name}: {instance.task.name}"
            async_task('telegram.tasks.send_message_to_user_sync', chat_id=chat_id, message=message_marketer)
        logging.info(f"Message sent to chat_id {chat_id}")

    except Exception as e:
        logging.error(f"Error sending message to chat_id {chat_id}: {e}")
        return f"Error sending message to chat_id {chat_id}: {e}"
