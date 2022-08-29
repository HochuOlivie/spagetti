from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import json
import os.path
import console
cfg = json.load(open("config.json", "r"))
from language_middleware import setup_middleware


# Загружаем настройки
if not os.path.exists('config.json'):
    console.fatalError('Settings file were not found')

storage = MemoryStorage()
bot = Bot(token=cfg['TG_TOKEN'])
dp = Dispatcher(bot, storage=storage)
i18n = setup_middleware(dp)
_ = i18n.gettext


