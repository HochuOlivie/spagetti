import sqlite3
import console
from datetime import datetime
from create_bot import cfg


async def addUser(token, telegram_id, username=''):
    # if await checkUserByToken(token) is True:
    #     console.printWarning(f"The user {username} already exists!")
    #     return False

    dt = datetime.now()
    ts = datetime.timestamp(dt)

    cur.execute(f'''
        INSERT INTO users (username, telegram_id, token, createAt, notification_news, notification_tickets, notification_payouts, notification_leads)
        VALUES ('{username}', '{telegram_id}', '{token}', '{ts}', 'true', 'true', 'true', 'true')
    ''');
    base.commit()
    return True


async def addUserLanguage(id, lang):
    cur.execute(f'''
            INSERT INTO users_lang (telegram_id, lang)
            VALUES ('{id}', '{lang}')
        ''');
    base.commit()
    return True


async def updateUserLang(id, lang):
    cur.execute(f'''UPDATE users_lang SET lang = '{lang}' WHERE telegram_id='{id}'
    ''')
    base.commit()
    return True


async def getUserLang(id):
    cur.execute(f'''
            SELECT lang FROM users_lang WHERE telegram_id='{id}'
        ''')
    res = cur.fetchone()
    if res:
        return res[0]
    return None


async def removeUserByTelegramId(id):
    cur.execute(f'''
        DELETE FROM users WHERE telegram_id='{id}'
    ''')
    base.commit()
    return True


async def removeUserByToken(token):
    cur.execute(f'''
        DELETE FROM users WHERE token='{token}'
    ''')
    base.commit()
    return True

async def checkUserByToken(token):
    cur.execute(f'''
        SELECT telegram_id FROM users WHERE token='{token}'
    ''')
    if cur.fetchone() is None:
        return False
    return True

async def checkUserByTelegramId(telegram_id):
    cur.execute(f'''
        SELECT telegram_id FROM users WHERE telegram_id='{telegram_id}'
    ''')
    if cur.fetchone() is None:
        return False
    return True

async def getTelegramIdByToken(token):
    cur.execute(f'''
        SELECT telegram_id FROM users WHERE token='{token}'
    ''')
    res = cur.fetchone()
    if res is None:
        console.printWarning("The user's token was not found")
        return None
    return res[0]

async def getTokenByTelegramId(telegram_id):
    cur.execute(f'''
        SELECT token FROM users WHERE telegram_id='{telegram_id}'
    ''')
    res = cur.fetchone()
    if res is None:
        console.printWarning("The user's telegramID was not found")
        return None
    return res[0]

async def getAllUsers():
    cur.execute(f'''
        SELECT * FROM users
    ''')
    res = cur.fetchall()

    list = []
    for user in res:
        list.append({
            "id": user[0],
            "name": user[1],
            "telegram_id": user[2],
            "token": user[3],
            "createAt": user[4],
            "notification_news": user[5],
            "notification_tickets": user[6],
            "notification_payouts": user[7],
            "notification_leads": user[8]
        })

    return list

async def setNotificationState(telegram_id, notification, state):
    if state is True or state == 'true':
        state = 'true'
    else:
        state = 'false'

    cur.execute(f'''
        UPDATE users SET notification_{notification}='{state}' WHERE telegram_id='{telegram_id}'
    ''')
    base.commit()
    return True

async def getNotigicationState(telegram_id, notification):
    cur.execute(f'''
        SELECT notification_{notification} FROM users WHERE telegram_id='{telegram_id}'
    ''')
    res = cur.fetchone()

    if res is None:
        console.printWarning("The user's telegramID was not found!")
        return None

    return res[0] == 'true'

async def toggleNotificationState(telegram_id, notification):
    state = True
    if await getNotigicationState(telegram_id, notification) is True:
        state = False
    await setNotificationState(telegram_id, notification, state)

def sql_start():
    global base, cur
    try:
        base = sqlite3.connect(cfg['DATABASE_NAME'])
        cur = base.cursor()

        if base:
            console.printSuccess('The database is open')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    telegram_id TEXT,
                    token TEXT,
                    createAt TEXT,
                    notification_news TEXT,
                    notification_tickets TEXT,
                    notification_payouts TEXT,
                    notification_leads TEXT
                )
            ''')
            cur.execute('''
                            CREATE TABLE IF NOT EXISTS users_lang (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                telegram_id TEXT,
                                lang TEXT
                            )
                        ''')

            # Фейковые пользователи
            # for x in range(10):
            #     cur.execute(f"INSERT INTO users (username, telegram_id, token) VALUES ('user{x}', 'tegid{x}', 'token{x}')")
            # base.commit()
    except sqlite3.Error as error:
        console.fatalError(f"Error when connecting to sqlite. {error}")

def sql_end():
    global base
    if base:
        base.close()
        console.printWarning('The database is close')
