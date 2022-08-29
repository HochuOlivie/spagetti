import requests
import json
import console
import database

async def checkToken(token):
    r = requests.get(f"https://api.cpagetti.com/wm/profile?token={token}");

    if r.status_code != 200:
        console.printWarning(f"Server response error. {r.text}")
        return None

    res = json.loads(r.text)
    return res['response']

async def getRequest(telegram_id, request, params=None):
    # Получаем токен пользователя
    token = await database.getTokenByTelegramId(telegram_id)
    if token is None:
        return None

    # Собираем запрос
    get_params = ''
    if params is not None:
        for key in params:
            get_params = f"{get_params}&{key}={params[key]}"

    # Отправляем запрос
    r = requests.get(f"https://api.cpagetti.com/wm/{request}?token={token}{get_params}");

    if r.status_code != 200:
        console.printWarning(f"Server response error. {r.text}")
        return None

    # Возвращаем в JSON
    return json.loads(r.text)

async def getInfoProfile(telegram_id):
    res = await getRequest(telegram_id, 'profile')
    if res is None:
        return res
    return res['response']

async def getBalance(telegram_id):
    res = await getRequest(telegram_id, 'balance')
    if res is None:
        return res
    return res['response']

async def getNews(telegram_id, offset=0, limit=100):
    res = await getRequest(telegram_id, 'news', {"limit":limit,"offset":offset,"sort":"-publishedAt"})
    if res is None:
        return res
    return res['response']

async def getStats(telegram_id, currency):
    res = await getRequest(telegram_id, 'stats', {"currency":currency})
    if res is None:
        return res
    return res['response']

async def getOffers(telegram_id, offset=0, limit=100):
    res = await getRequest(telegram_id, 'offers', {"limit":limit,"offset":offset})
    if res is None:
        return res
    return res['response'], res['info']

async def getPersonalOffers(telegram_id):
    res = await getRequest(telegram_id, 'offers', {'limit':10})
    if res is None:
        return res
    return res['response']

async def getStreams(telegram_id, offset=0, limit=100):
    res = await getRequest(telegram_id, 'streams', {"limit":limit,"offset":offset,"sort":"-createdAt"})
    if res is None:
        return res
    return res['response'], res['info']

async def getPayouts(telegram_id, offset=0, limit=100):
    res = await getRequest(telegram_id, 'payouts', {"limit": limit, "offset": offset, "sort": "-date"})
    if res is None:
        return res
    return res['response'], res['info']

async def sendWithdrawal(telegram_id, data):
    res = await getRequest(telegram_id, 'withdrawal', data)
    if res is None:
        return res
    return res['response']

async def sendConfirmCode(telegram_id, code):
    res = await getRequest(telegram_id, 'confirmcode', {"code": code})
    if res is None:
        return res
    return res['response']