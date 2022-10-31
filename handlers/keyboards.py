from create_bot import cfg
from aiogram import types
from aiogram.types import KeyboardButton, InlineKeyboardButton

import database
import utils
import caption
from importlib import reload
from create_bot import _

reload(caption)

markup_remove = types.ReplyKeyboardRemove()

get_token_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
get_token_btn1 = KeyboardButton(caption.input_token)
get_token_btn2 = KeyboardButton(caption.run_without_token)
get_token_keyboard.add(get_token_btn1, get_token_btn2)

main_menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_btn1 = [caption.my_account, caption.instructions]
main_menu_btn2 = [caption.notifications, caption.contacts]
main_menu_keyboard.row(*main_menu_btn1)
main_menu_keyboard.row(*main_menu_btn2)

choose_lang_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
lang_russian = KeyboardButton(caption.russian)
lang_english = KeyboardButton(caption.english)
choose_lang_keyboard.add(lang_russian, lang_english)


account_keyboard = types.InlineKeyboardMarkup(row_width=1)
account_btn1 = InlineKeyboardButton(caption.balance, callback_data="show_balance")
account_btn2 = InlineKeyboardButton(caption.news, callback_data='{"action":"news","offset":"0"}')
account_btn3 = InlineKeyboardButton(caption.stats, callback_data="show_stats")
account_btn4 = InlineKeyboardButton(caption.offers, callback_data='{"action":"offers","offset":"0"}')
account_btn5 = InlineKeyboardButton(caption.streams, callback_data='{"action":"streams","offset":"0"}')
account_btn6 = InlineKeyboardButton(caption.payouts, callback_data='{"action":"payouts","offset":"0"}')
# account_btn7 = InlineKeyboardButton(caption.personal_offers, callback_data="show_personal_offers")
account_btn8 = InlineKeyboardButton(caption.logout, callback_data="logout")
account_keyboard.add(account_btn1, account_btn2, account_btn3, account_btn4,
                     account_btn5, account_btn6,
                     account_btn8
                     )

stats_keyboard = types.InlineKeyboardMarkup(row_width=1)
stats_btn1 = InlineKeyboardButton(caption.RUB, callback_data='{"action":"stats","currency":"RUB"}')
stats_btn2 = InlineKeyboardButton(caption.USD, callback_data='{"action":"stats","currency":"USD"}')
stats_keyboard.add(stats_btn1, stats_btn2)

async def get_name_notification(telegram_id, notification, caption):
    state = await database.getNotigicationState(telegram_id, notification)

    if state is True:
        return '✅ ' + caption
    return '❌ ' + caption

async def get_notifications(telegram_id):
    menu = types.InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(await get_name_notification(telegram_id, 'news', caption.notify_news), callback_data='{"action":"notification","type":"news"}')
    btn2 = InlineKeyboardButton(await get_name_notification(telegram_id, 'tickets', caption.notify_tickets), callback_data='{"action":"notification","type":"tickets"}')
    btn3 = InlineKeyboardButton(await get_name_notification(telegram_id, 'payouts', caption.notify_payouts), callback_data='{"action":"notification","type":"payouts"}')
    btn4 = InlineKeyboardButton(await get_name_notification(telegram_id, 'leads', caption.notify_leads), callback_data='{"action":"notification","type":"leads"}')
    menu.add(btn1, btn2, btn3, btn4)
    return menu


async def get_main_menu(telegram_id, locale=None):

    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if await database.checkUserByTelegramId(telegram_id):
        btn1 = [_(caption.my_account, locale=locale), _(caption.instructions, locale=locale)]
        btn2 = [_(caption.notifications, locale=locale), _(caption.contacts, locale=locale)]
    else:
        btn1 = [_(caption.contacts, locale=locale), _(caption.instructions, locale=locale)]
        btn2 = [_(caption.auth, locale=locale)]

    menu.row(*btn1).row(*btn2)
    return menu


async def get_instructions():
    menu = types.InlineKeyboardMarkup(row_width=1)
    instructions = await utils.getInstructions()

    if 'data' not in instructions:
        return menu

    for x, btn in enumerate(instructions['data']):
        btn = InlineKeyboardButton(btn['title'], callback_data='{"action":"show_instruction","id":"' + str(x) + '"}')
        menu.add(btn)
    return menu


async def get_contacts():
    menu = types.InlineKeyboardMarkup(row_width=1)
    contacts = await utils.getContacts()

    if 'data' not in contacts:
        return menu

    for x, btn in enumerate(contacts['data']):
        btn = InlineKeyboardButton(btn['title'], callback_data='{"action":"show_contacts","id":"' + str(x) + '"}')
        menu.add(btn)
    return menu


async def currency_balance(balance):
    menu = types.InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"{caption.RUB} ({balance['RUB']})", callback_data=f"action_currency:RUB:{balance['RUB']}")
    btn2 = InlineKeyboardButton(f"{caption.USD} ({balance['USD']})", callback_data=f"action_currency:USD:{balance['USD']}")
    menu.add(btn1, btn2)
    return menu

async def get_purse():
    menu = types.InlineKeyboardMarkup(row_width=1)

    for payment in cfg['PAYMENTS']:
        btn_tmp = InlineKeyboardButton(cfg['PAYMENTS'][payment]['name'], callback_data=f"purse:{payment}:{cfg['PAYMENTS'][payment]['name']}")
        menu.add(btn_tmp)

    return menu

async def get_int_list():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [ '100', '200', '500', '1000', '1500', '2000', '2500' ]
    menu.add(*btns)
    return menu

async def withdrawal_check():
    menu = types.InlineKeyboardMarkup(row_width=1)
    btns = [
        InlineKeyboardButton('Вывести', callback_data='withdrawal:yes'),
        InlineKeyboardButton('Отменить', callback_data='withdrawal:no')
    ]
    for btn in btns:
        menu.add(btn)
    return menu

async def withdrawal_repeat():
    menu = types.InlineKeyboardMarkup(row_width=1)
    btn = InlineKeyboardButton('Отправить код еще раз', callback_data='withdrawal:repeat')
    menu.add(btn)
    return menu