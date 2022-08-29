from handlers import admin
from create_bot import cfg
import asyncio
import database
import utils
import json
import console

server = None


async def generateResponse(success, status, response=None, message=''):
    res = {}
    res['status'] = status

    if success is True:
        res['success'] = 'true'
    else:
        res['success'] = 'false'

    if message is not None and len(message) > 0:
        res['message'] = message

    if response is None:
        res['response'] = []
    else:
        res['response'] = response

    return json.dumps(res)

async def server_send(msg, writer):
    writer.write(msg.encode())
    await writer.drain()
    writer.close()

async def server_processor(reader, writer):
    message = ''

    try:
        while True:
            data_tmp = await reader.read(100);
            message = message + data_tmp.decode()
            if len(data_tmp.decode()) < 100:
                break
    except Exception as error:
        console.printError('server_processor():' + str(error))
        msg = await generateResponse(False, 500, None, str(error))
        await server_send(msg, writer)
        return

    commands = None
    try:
        commands = json.loads(message)
    except Exception as error:
        msg = await generateResponse(False, 403, None, 'Forbidden')
        await server_send(msg, writer)
        return

    if commands['token'] != cfg['SITE_TOKEN']:
        msg = await generateResponse(False, 403, None, 'Forbidden')
        await server_send(msg, writer)
        return

    if 'action' not in commands:
        msg = await generateResponse(False, 403, None, 'Forbidden')
        await server_send(msg, writer)
        return

    msg = await generateResponse(False, 200, None, 'Unknown command')
    cmd = commands['action'].lower()

    # Получение списка пользователей
    if cmd == 'getusers':
        msg = await generateResponse(True, 200, await database.getAllUsers())

    # Отправка сообщения пользователю
    elif cmd == 'sendmessage':
        users = None
        if 'users' in commands:
            users = commands['users']

        # res = [success(bool), except(string)]
        res = await admin.serv_sendMessage(users, commands['data'])

        if res[0] is False:
            msg = await generateResponse(False, 200, None, res[1])
        else:
            msg = await generateResponse(True, 200, None, None)

    # Отправка уведомления пользователю
    elif cmd == 'sendnotification':
        res = await admin.serv_sendNotification(commands)

        if res[0] is False:
            msg = await generateResponse(False, 200, None, res[1])
        else:
            msg = await generateResponse(True, 200, None, None)

    # Отправка инструкций
    elif cmd == 'getinstructions':
        msg = await generateResponse(True, 200, await utils.getInstructions())

    # Обновить инструкции
    elif cmd == 'updateinstructions':
        res = await utils.updateInstructions(commands)

        if res[0] is False:
            msg = await generateResponse(False, 200, None, res[1])
        else:
            msg = await generateResponse(True, 200, None, None)

    # Отправка контактов
    elif cmd == 'getcontacts':
        msg = await generateResponse(True, 200, await utils.getContacts())

    # Обновить контакты
    elif cmd == 'updatecontacts':
        res = await utils.updateContacts(commands)

        if res[0] is False:
            msg = await generateResponse(False, 200, None, res[1])
        else:
            msg = await generateResponse(True, 200, None, None)

    await server_send(msg, writer)

async def loop():
    if server is None:
        return
    await server.serve_forever()

async def init():
    server = await asyncio.start_server(server_processor, cfg['SERVER_IP'], 8888)
    addr = server.sockets[0].getsockname()
    console.printSuccess(f"Serving on {addr}")
