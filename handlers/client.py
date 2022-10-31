from aiogram import Dispatcher, types

import utils
from create_bot import cfg, bot, dp, _
from handlers import keyboards, admin
import console
import database
import api
import json
import re
import caption
import sys
from importlib import reload
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def go_auth(telegram_id):
    reload(keyboards)
    await bot.send_message(telegram_id, _('Вы не авторизированы!'), reply_markup=keyboards.get_token_keyboard)


async def command_start(message: types.Message):
    reload(keyboards)
    await bot.send_message(message.from_user.id, 'Выберите язык/Choose language', reply_markup=keyboards.choose_lang_keyboard)


async def command_account(message: types.Message):
    reload(keyboards)
    if await database.checkUserByTelegramId(message.from_user.id) is False:
        await go_auth(message.from_user.id)
        return

    await bot.send_message(message.from_user.id, _('Управление вашим аккаунтом'), reply_markup=keyboards.account_keyboard)

# ================ БАЛАНС ================ #
async def command_show_balance(callback: types.CallbackQuery):
    balance = await api.getBalance(callback.from_user.id)

    if balance is None:
        await bot.send_message(callback.from_user.id, _('Произошла ошибка'))
        return

    await bot.send_message(callback.from_user.id, _('''
Ваш баланс:
{}: {}
{}: {}
'''.format(caption.RUB, balance['RUB'], caption.USD, balance['USD'])))

# ================ НОВОСТИ ================ #
async def command_show_news(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"news"'):
        limit = 5
        data = json.loads(callback.data)
        news_list = await api.getNews(callback.from_user.id, data["offset"], limit)
        count = 0
        for news_item in news_list:
            count = count + 1
            text = _('''
*{}*

{}

_Дата: {}_
            '''.format(news_item['title'], news_item['spoiler'], news_item['publishedAt']))
            text = re.sub(r'\<[^>]*\>', '', text)
            text = re.sub('&nbsp;', ' ', text)


            markup = None
            if count == limit:
                # Добавляем кнопку "Показать еще"
                new_offset = int(data["offset"]) + limit
                markup = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(_('Показать еще'), callback_data='{"action":"news","offset":"' + str(new_offset) + '"}')
                markup.add(button)

            await bot.send_message(callback.from_user.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        await bot.send_message(callback.from_user.id, _('Произошла ошибка'))

# ================ СТАТИСТИКА ================ #
async def command_show_stats(callback: types.CallbackQuery):
    reload(keyboards)
    await bot.send_message(callback.from_user.id, _("В какой валюте льешь траф?"), reply_markup=keyboards.stats_keyboard)

async def command_show_stats_rub(callback: types.CallbackQuery):
    reload(keyboards)
    await callback.message.edit_text(callback.message.text)
    if callback.data and callback.data.startswith('{"action":"stats"'):
        data = json.loads(callback.data)
        if 'offset' in data:
            offset = int(data['offset'])
        else:
            offset = 0
        stats_list = await api.getStats(callback.from_user.id, data["currency"])
        stats_list = sorted(stats_list, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)[offset:]
        # found = False
        msg_arr = []
        if offset == 0:
            last_date = datetime.now() - timedelta(days=6)
        else:
            try:
                last_date = datetime.strptime(stats_list[offset - 1]['date'], '%Y-%m-%d')
            except:
                await bot.send_message(callback.from_user.id, 'Нет данных')
                return
        for stats_item in stats_list:
            offset += 1
            curr_date = datetime.strptime(stats_item['date'], '%Y-%m-%d')
            if stats_item['leadsTotal'] is None:
                #await bot.send_message(callback.from_user.id, f"Дата: {stats_item['date']}\nНет данных")
                continue
            if curr_date <= last_date:
                break
            aprove = round(float(stats_item['ratioApprove']) * 100, 2)
            msg_arr.append(_('''
Дата: {}
Всего лидов: {}
Валидные: {}
В работе: {}
Невалидные: {}
Подтвержденные: {}
Отклонено: {}
Треш: {}

Финансы:
В работе: {}
Подтвержденные: {}
Отклонено: {}
Апрув: {}%
            '''.format(stats_item['date'], stats_item['leadsTotal'], stats_item['leadsValidUser'], stats_item['leadsValid'],
                       stats_item['leadsInvalid'], stats_item['leadsConfirmed'],
                       stats_item['leadsDeclined'],
                       stats_item['leadsTrash'],
                       stats_item['salaryValid'],
                       stats_item['salaryConfirmed'],
                       stats_item['salaryDeclined'],
                       aprove
                       )))
        for msg_id in range(len(msg_arr) - 1):
            await bot.send_message(callback.from_user.id, msg_arr[msg_id])
        print(msg_arr)
        print(msg_arr[-1])
        await bot.send_message(callback.from_user.id, msg_arr[len(msg_arr) - 1], reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton('Показать еще', callback_data='{"action":"stats","offset":"' + str(offset) + '","currency":"' + data["currency"] + '"}'
        )))
        # if found is False:
        #     await bot.send_message(callback.from_user.id, _("Нет данных"))
    else:
        await bot.send_message(callback.from_user.id, _('Произошла ошибка'))


# ================ ОФФЕРЫ ================ #
async def command_show_offers(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"offers"'):
        data = json.loads(callback.data)
        limit = 5
        count = 0
        offers, info = await api.getOffers(callback.from_user.id, data["offset"], limit)
        if data['offset'] == '0':
            await bot.send_message(callback.from_user.id, _("Всего {} офферов!".format(info['total'])))
        for id in offers:
            count = count + 1

            markup = None
            if count == limit:
                # Добавляем кнопку "Показать еще"
                reside = str(int(info['total']) - int(data['offset']))
                new_offset = int(data["offset"]) + limit
                markup = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(_("Показать еще ({})".format(reside)), callback_data='{"action":"offers","offset":"' + str(
                    new_offset) + '"}')
                markup.add(button)

            msg = _('''
ID: {}
Название: {}

URL: https://cpagetti.com/offer/view/{}
            '''.format(offers[id]['id'], offers[id]['name'], offers[id]['id']))

            if offers[id]['logo'] is None:
                await bot.send_message(callback.from_user.id, msg, parse_mode="HTML", reply_markup=markup)
            else:
                await bot.send_photo(callback.from_user.id, offers[id]['logo'], msg, parse_mode="HTML", reply_markup=markup)
    else:
        await bot.send_message(callback.from_user.id, _('Произошла ошибка'))


# ================ ПОТОКИ ================ #
async def command_show_streams(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"streams"'):
        data = json.loads(callback.data)
        limit = 5
        count = 0
        streams, info = await api.getStreams(callback.from_user.id, data["offset"], limit)
        if data['offset'] == '0':
            await bot.send_message(callback.from_user.id, _("Всего {} потоков!".format(info['total'])))
        for item in streams:
            count = count + 1

            markup = None
            if count == limit:
                # Добавляем кнопку "Показать еще"
                reside = str(int(info['total']) - int(data['offset']))
                new_offset = int(data["offset"]) + limit
                markup = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(_("Показать еще ({})".format(reside)), callback_data='{"action":"streams","offset":"' + str(
                    new_offset) + '"}')
                markup.add(button)

            link = item['url'].split('?')[0]
            await bot.send_message(callback.from_user.id, _('''
Создан: {}
Название: {}
ID оффера: {}
Имя оффера: {}
URL: {}
            '''.format(item['createdAt'], item['name'], item['offerId'], item['offerName'], link)), reply_markup=markup)
    else:
        await bot.send_message(callback.from_user.id, _('Произошла ошибка'))

# ================ ВЫПЛАТЫ ================ #
async def command_show_payouts(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"payouts"'):
        data = json.loads(callback.data)
        limit = 5
        count = 0
        payouts, info = await api.getPayouts(callback.from_user.id, data["offset"], limit)
        if data['offset'] == '0':
            await bot.send_message(callback.from_user.id, _("Всего {} выплат!".format(info['total'])))
        for item in payouts:
            count = count + 1

            markup = None
            if count == limit:
                # Добавляем кнопку "Показать еще"
                reside = str(int(info['total']) - int(data['offset']))
                new_offset = int(data["offset"]) + limit
                markup = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(_("Показать еще ({})".format(reside)), callback_data='{"action":"payouts","offset":"' + str(new_offset) + '"}')
                markup.add(button)

            msg = _('''
ID: {}
Дата: {}
Сумма: {} {}
Статус: {}
            '''.format(item['id'], item['date'], item['sum'], item['currency'], item['status']))

            await bot.send_message(callback.from_user.id, msg, parse_mode="HTML", reply_markup=markup)
    else:
        await bot.send_message(callback.from_user.id, _('Произошла ошибка'))

# ================ ПОДБОРКА ОФФЕРОВ ================ #
# async def command_show_personal_offers(callback: types.CallbackQuery):
#     offers = await api.getPersonalOffers(callback.from_user.id)
#     await bot.send_message(callback.from_user.id, 'Ваша персональная подборка офферов!')
#     for id in offers:
#         msg = f'''
# ID: {offers[id]['id']}
# Название: {offers[id]['name']}

# URL: https://cpagetti.com/offer/view/{offers[id]['id']}
  #       '''

        # if offers[id]['logo'] is None:
        #     await bot.send_message(callback.from_user.id, msg, parse_mode="HTML")
        # else:
        #     await bot.send_photo(callback.from_user.id, offers[id]['logo'], msg, parse_mode="HTML")

# ================ УВЕДОМЛЕНИЯ ================ #
async def show_notifications(message: types.Message):
    reload(keyboards)
    if await database.checkUserByTelegramId(message.from_user.id) is False:
        await go_auth(message.from_user.id)
        return
    mark = await keyboards.get_notifications(message.from_user.id)
    await bot.send_message(message.from_user.id, _('Уведомлять меня о следующих событиях:'), reply_markup=mark)

async def command_toggle_notification(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"notification"'):
        data = json.loads(callback.data)
        await database.toggleNotificationState(callback.from_user.id, data['type'])
        menu = await keyboards.get_notifications(callback.from_user.id)
        await callback.message.edit_reply_markup(menu)

# ================ ИНСТРУКЦИИ ================ #
async def command_instructions(message: types.Message):
    reload(keyboards)
    instructions = await utils.getInstructions()
    menu = await keyboards.get_instructions()
    caption = ''
    if 'text' in instructions:
        caption = instructions['text']
    await bot.send_message(message.from_user.id, caption, reply_markup=menu)


async def command_show_instruction(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"show_instruction"'):
        instructions = await utils.getInstructions()

        data = json.loads(callback.data)
        msg = instructions['data'][int(data['id'])]

        # if 'data' not in msg_list:
        #     console.printError('command_show_instruction(): Message is empty!')
        #     await bot.send_message(callback.from_user.id, _('Произошла ошибка...'))
        #     return

        # msg
        if 'photo' in msg and msg['photo'] or 'video' in msg and msg['video'] or 'document' in msg and msg['document'] or 'animation' in msg and msg['animation']:
            # gen_msg = [success(bool), type(string), message(InputMedia|string)]
            gen_msg = await admin.serv_generateMessage1(msg)

            if gen_msg[0] is True:
                if 'text' in msg:
                    gen_msg[2][0]['caption'] = re.sub(r'</?(span|p|sub|sup|blockquote|br|ol|li|ul)[^>]*>', '', msg['text'])
                gen_msg[2][0]['parse_mode'] = 'HTML'
                await admin.sendMessage(callback.from_user.id, gen_msg[1], gen_msg[2])
            else:
                console.printWarning('command_show_instruction(): ParseError: {}'.format(msg))
        elif 'text' in msg:
            await admin.sendMessage(callback.from_user.id, 'text', msg['text'])
        else:
            console.printWarning('command_show_instruction(): ParseError: {}'.format(msg))


# ================ КОНТАКТЫ ================ #
async def command_contacts(message: types.Message):
    reload(keyboards)
    contacts = await utils.getContacts()
    menu = await keyboards.get_contacts()
    caption = ''
    if 'text' in contacts:
        caption = contacts['text']
    await bot.send_message(message.from_user.id, caption, reply_markup=menu)


async def command_show_contacts(callback: types.CallbackQuery):
    reload(keyboards)
    if callback.data and callback.data.startswith('{"action":"show_instruction"'):
        contacts = await utils.getContacts()

        data = json.loads(callback.data)
        msg_list = contacts['data'][int(data['id'])]

        if 'data' not in msg_list:
            console.printError('command_show_contacts(): Message is empty!')
            await bot.send_message(callback.from_user.id, _('Произошла ошибка...'))
            return

        for msg in msg_list['data']:
            if 'media' in msg:
                # gen_msg = [success(bool), type(string), message(InputMedia|string)]
                gen_msg = await admin.serv_generateMessage(msg['media'])

                if gen_msg[0] is True:
                    if 'text' in msg:
                        gen_msg[2][0]['caption'] = msg['text']
                    gen_msg[2][0]['parse_mode'] = 'Markdown'
                    await admin.sendMessage(callback.from_user.id, gen_msg[1], gen_msg[2])
                else:
                    console.printWarning('command_show_contacts(): ParseError: {}'.format(msg))
            elif 'text' in msg:
                await admin.sendMessage(callback.from_user.id, 'text', msg['text'])
            else:
                console.printWarning('command_show_contacts(): ParseError: {}'.format(msg))


async def command_logout(callback: types.CallbackQuery):
    reload(keyboards)
    await database.removeUserByTelegramId(callback.from_user.id)
    await bot.send_message(callback.from_user.id, 'Выберите язык/Choose language',
                           reply_markup=keyboards.choose_lang_keyboard)


async def command_russian(message: types.Message):
    if await database.getUserLang(message.from_user.id):
        await database.updateUserLang(message.from_user.id, 'ru')
    else:
        await database.addUserLanguage(message.from_user.id, 'ru')
    print('-----')
    await greetings(message)


async def command_english(message: types.Message):
    if await database.getUserLang(message.from_user.id):
        await database.updateUserLang(message.from_user.id, 'en')
    else:
        await database.addUserLanguage(message.from_user.id, 'en')
    print('-----')
    await greetings_eng(message)


async def greetings(message: types.Message):
    reload(keyboards)
    # Проверяем наличие пользователя в БД
    if await database.checkUserByTelegramId(message.from_user.id):
        # Проверяем акутальность его токена
        token = await database.getTokenByTelegramId(message.from_user.id)
        profile = await api.checkToken(token)
        if profile is not None:
            menu = await keyboards.get_main_menu(message.from_user.id, locale='ru')
            await bot.send_message(message.from_user.id,
                                   "👋 Приветствую {}. Я - твой помощник Сэр Макарон 🧐. Здесь вы можете управлять данными в своем кабинете!".format(
                                       profile['firstName']), reply_markup=menu)
            return
        # Удаляет из БД пользователя, потому что токен не подошел
        else:
            await database.removeUserByToken(token)

    await bot.send_message(message.from_user.id,
                           "👋 Приветствую. Я - твой помощник Сэр Макарон 🧐. Здесь ты можешь управлять данными в своем кабинете. Для того, чтобы я мог тебе помочь, тебе нужно осуществить вход по API токену (возьми его у своего менеджера).",
                           reply_markup=keyboards.get_token_keyboard)


async def greetings_eng(message: types.Message):
    reload(keyboards)
    # Проверяем наличие пользователя в БД
    if await database.checkUserByTelegramId(message.from_user.id):
        # Проверяем акутальность его токена
        token = await database.getTokenByTelegramId(message.from_user.id)
        profile = await api.checkToken(token)
        if profile is not None:
            menu = await keyboards.get_main_menu(message.from_user.id, locale='en')
            await bot.send_message(message.from_user.id,
                                   "👋 Greetings {}. I am your assistant Sir Macaron 🧐. You can manage data in your account!".format(
                                       profile['firstName']), reply_markup=menu)
            return
        # Удаляет из БД пользователя, потому что токен не подошел
        else:
            await database.removeUserByToken(token)

    await bot.send_message(message.from_user.id,
                           "👋 Greetings. I am your assistant Sir Macaron 🧐. Here you can manage the data in your account. In order for me to help you, you need to log in using the API token (take it from your manager).",
                           reply_markup=keyboards.get_token_keyboard)


def register_handlers():
    dp.register_message_handler(command_start, commands=['start'])

    dp.register_message_handler(command_russian, text=caption.russian)
    dp.register_message_handler(command_english, text=caption.english)

    dp.register_message_handler(command_account, text=[_(caption.my_account, locale='en'), _(caption.my_account, locale='ru')])
    dp.register_callback_query_handler(command_show_balance, text='show_balance')
    dp.register_callback_query_handler(command_show_news, text_contains='{"action":"news"')
    dp.register_callback_query_handler(command_show_stats, text='show_stats')
    dp.register_callback_query_handler(command_show_stats_rub, text_contains='{"action":"stats"')
    dp.register_callback_query_handler(command_show_offers, text_contains='{"action":"offers"')
    dp.register_callback_query_handler(command_show_payouts, text_contains='{"action":"payouts"')
    dp.register_callback_query_handler(command_show_streams, text_contains='{"action":"streams"')
    dp.register_callback_query_handler(command_logout, text='logout')
 #    dp.register_callback_query_handler(command_show_personal_offers, text='show_personal_offers')
    dp.register_message_handler(command_instructions, text=[_(caption.instructions, locale='en'), _(caption.instructions, locale='ru')])
    dp.register_callback_query_handler(command_show_instruction, text_contains='{"action":"show_instruction"')
    dp.register_message_handler(command_contacts, text=[_(caption.contacts, locale='en'), _(caption.contacts, locale='ru')])
    dp.register_callback_query_handler(command_show_contacts, text_contains='{"action":"show_contacts"')
    dp.register_message_handler(show_notifications, text=[_(caption.notifications   , locale='en'), _(caption.notifications, locale='ru')])
    dp.register_callback_query_handler(command_toggle_notification, text_contains='{"action":"notification"')