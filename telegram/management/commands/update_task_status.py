from django.core.management.base import BaseCommand
from django.utils import timezone
from telegram.models import EmployeeTask, TaskHistory, Employee
from aiogram import Bot
from dotenv import load_dotenv
import os
load_dotenv()
API_TOKEN = os.getenv('TOKEN')
bot = Bot(token=API_TOKEN)

class Command(BaseCommand):
    help = 'Update task status'

    def handle(self, *args, **kwargs):
        # get all tasks
        tasks = EmployeeTask.objects.all()
        for task in tasks:
            # check if task is overdue
            if task.deadline < timezone.now():
                if task.deadline:
                    task.status = EmployeeTask.STATUS_CHOICES[3][0]  # просрочено
                    task.save()
                    task_history = TaskHistory.objects.create(employee=tasks.employee, task=task.task)
                    task_history.save()
                    employee = Employee.objects.get(id=task.employee.id)
                    employee.strike += 2
                    employee.save()
                    print(f"Task {task.task.name} is overdue")
                    bot.send_message(chat_id=employee.chat_id, text=f"Задача {task.task.name} просрочена, ваш штраф: {employee.strike} баллов")