from django.core.management.base import BaseCommand
from telegram.bot_logic import start_bot
import asyncio

class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Telegram bot...")
        asyncio.run(start_bot())

