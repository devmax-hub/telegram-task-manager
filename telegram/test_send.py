from telegram.models import EmployeeTask, Employee
from aiogram import Bot

load_dotenv()

API_TOKEN = os.getenv('TOKEN')
bot = Bot(token=API_TOKEN)
async def send_employee_task_notification():
    instance = EmployeeTask.objects.first()
    employee = instance.employee
    chat_id = employee.chat_id
    message_employee = "У вас появилась новая задача: {}".format(instance.task.name)
    await bot.send_message(chat_id=chat_id, text=message_employee)
if __main__ == '__main__':
    send_employee_task_notification()
    pass