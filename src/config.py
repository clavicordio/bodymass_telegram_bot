import os
from telebot import asyncio_helper

SQLITE_PATH = 'data/bodymass.db'
MAX_FILE_SIZE = 100*1024
MAX_BODY_WEIGHT = 1000
MAINTENANCE_THRESHOLD = 0.001

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
# LANGUAGE = os.environ.get('BODY_MASS_BOT_LANGUAGE') or 'ENG'


class TelegramTokenNotSpecified(Exception):
    pass

if not TELEGRAM_TOKEN:
    raise TelegramTokenNotSpecified("Please specify TELEGRAM_TOKEN environmental variable or edit src/config.py")

if os.environ.get('PYTHONANYWHERE'):
    asyncio_helper.proxy = "http://proxy.server:3128"
