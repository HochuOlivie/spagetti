from aiogram.utils import executor
from create_bot import cfg, dp
from handlers import client, admin
from dotenv import load_dotenv
import console
import database
import asyncio
import server
import os
import aioschedule

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

async def task():
    while True:
        await server.loop()
        await asyncio.sleep(1)

async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    # Создаем сервер для общения с сайтом
    await server.init()
    asyncio.create_task(scheduler())
    console.printSuccess(f"{cfg['BOT_NAME']} {cfg['BOT_VER_STRING']} активен!")

async def on_shutdown(_):
    database.sql_end()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(task())

    database.sql_start()
    admin.register_handlers()
    client.register_handlers()
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, timeout=1)
