from aiogram import Bot
from dotenv import load_dotenv
import os
import logging
import asyncio
load_dotenv()
API_TOKEN = os.getenv('TOKEN')
bot = Bot(token=API_TOKEN)

async def send_messages_to_user(instance):
    try:
        if instance.employee is None:
            return
        employee = instance.employee
        employee_chat_id = employee.chat_id
        message = f"У вас по задаче: {instance.task.name}"
        logging.info(f"Sending message to employee chat_id {employee_chat_id}: {message}")
        await asyncio.run(bot.send_message(chat_id=employee_chat_id, text=message))

    except Exception as e:
        logging.error(f"Error sending message to employee chat_id {employee_chat_id}: {e}")

def send_message_to_user_sync(chat_id, message):
    try:
        logging.info(f"Sending message to chat_id {chat_id}: {message}")
        asyncio.run(bot.send_message(chat_id=chat_id, text=message))

    except Exception as e:
        logging.error(f"Error sending message to employee chat_id {chat_id}: {e}")