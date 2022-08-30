from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from handlers import keyboards
from create_bot import cfg, bot, dp
import console
import api
import database
import caption
import messages
import aioschedule
import re
from create_bot import _


class FSMAdmin(StatesGroup):
    token = State()

class FSMWithdrawal(StatesGroup):
    currency = State()
    count = State()
    purse = State()
    pursedata = State()
    confirm = State()
    smscode = State()
    key = State()

async def set_token(message: types.Message):
    if await database.checkUserByTelegramId(message.from_user.id):
        menu = await keyboards.get_main_menu(message.from_user.id)
        await bot.send_message(message.from_user.id, "Вы уже авторизированы!", reply_markup=menu)
        return

    await bot.send_message(message.from_user.id, "Укажите API TOKEN полученный от вашего менеджера\n\n/cancel - Отмена операции", reply_markup=keyboards.markup_remove)
    await FSMAdmin.token.set()

async def without_token(message: types.Message):
    keys = await keyboards.get_main_menu(message.from_user.id)
    await bot.send_message(message.from_user.id, 'Доступные функции', reply_markup=keys)

async def check_token(message: types.Message, state: FSMContext):
    info = await api.checkToken(message.text)
    if info is not None:
        await database.addUser(message.text, message.from_user.id, info['firstName'])
        await bot.send_message(message.from_user.id, f"👋 Приветствую {info['firstName']}! Твой API Token добавлен. Теперь ты можешь пользоваться всеми функциями.", reply_markup=keyboards.main_menu_keyboard)
        console.printSuccess(f"Append user {message.from_user.id}")
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, "Извините, введенный вами API Token не найден")
        # await FSMAdmin.token.set()

    async with state.proxy() as data:
        data['token'] = message.text

async def check_token_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()

    aioschedule.clear(f'smscode_repeat_{message.from_user.id}')

    if await database.checkUserByTelegramId(message.from_user.id):
        await bot.send_message(message.from_user.id, "Операция отменена", reply_markup=await keyboards.get_main_menu(message.from_user.id))
    else:
        await bot.send_message(message.from_user.id, "Операция отменена", reply_markup=keyboards.get_token_keyboard)

async def auth(message: types.Message):
    if await database.checkUserByTelegramId(message.from_user.id):
        menu = await keyboards.get_main_menu(message.from_user.id)
        await bot.send_message(message.from_user.id, "Вы уже авторизированы!", reply_markup=menu)
        return

    await bot.send_message(message.from_user.id, "🔐 Укажите API TOKEN полученный от вашего менеджера", reply_markup=keyboards.get_token_keyboard)

# ================ ВЫВОД СРЕДСТВ ================ #
async def command_withdrawal(callback: types.CallbackQuery):
    balance = await api.getBalance(callback.from_user.id)

    if balance is None:
        await bot.send_message(callback.from_user.id, 'Произошла ошибка')
        return

    btns = await keyboards.currency_balance(balance)
    await bot.send_message(callback.from_user.id, messages.withdrawal_balance, reply_markup=btns)
    await FSMWithdrawal.currency.set()
    await bot.send_message(callback.from_user.id, messages.cancel, reply_markup=keyboards.markup_remove)

async def command_withdrawal_currency(callback: types.CallbackQuery, state: FSMWithdrawal.currency):
    input = callback.data.split(':')
    async with state.proxy() as data:
        data['currency'] = input[1]
        data['maxcount'] = float(input[2])
    await FSMWithdrawal.next()
    await bot.send_message(callback.from_user.id, messages.withdrawal_count, reply_markup=await keyboards.get_int_list())

async def command_withdrawal_count(message: types.Message, state: FSMWithdrawal.count):
    try:
        input = int(message.text)
    except Exception as error:
        await bot.send_message(message.from_user.id, messages.withdrawal_count_err, reply_markup=await keyboards.get_int_list())
        return

    if input <= 0:
        await bot.send_message(message.from_user.id, messages.withdrawal_count_errmin, reply_markup=await keyboards.get_int_list())
        return

    async with state.proxy() as data:
        if input > data['maxcount']:
            await bot.send_message(message.from_user.id, messages.withdrawal_count_errmax, reply_markup=await keyboards.get_int_list())
            return
        data['count'] = input

        await bot.send_message(message.from_user.id, await messages.withdrawal_willpay(input, data['currency']), reply_markup=keyboards.markup_remove)
    await FSMWithdrawal.next()
    await bot.send_message(message.from_user.id, messages.withdrawal_purse, reply_markup=await keyboards.get_purse())

async def command_withdrawal_choise_purse(callback: types.CallbackQuery, state: FSMWithdrawal.purse):
    input = callback.data.split(':')

    async with state.proxy() as data:
        data['payment'] = input[1]
        data['payment_name'] = input[2]
    await FSMWithdrawal.next()
    await bot.send_message(callback.from_user.id, messages.withdrawal_pursedata, reply_markup=keyboards.markup_remove)

async def command_withdrawal_checkdata(message: types.Message, state: FSMWithdrawal.pursedata):
    input = message.text
    async with state.proxy() as data:
        if cfg['PAYMENTS'][data['payment']]['pattern'] != 'text':
            res = re.match(cfg['PAYMENTS'][data['payment']]['pattern'], input)
            if res is None:
                await bot.send_message(message.from_user.id, await messages.withdrawal_purse_invalid(cfg['PAYMENTS'][data['payment']]['example']), parse_mode='Markdown')
                return
            else:
                input = res.group(0)

        data['payment_data'] = input
        await bot.send_message(message.from_user.id, await messages.withdrawal_checkdata(data), reply_markup=await keyboards.withdrawal_check())
    await FSMWithdrawal.next()

async def command_withdrawal_confirm(callback: types.CallbackQuery, state: FSMWithdrawal.confirm):
    input = callback.data.split(':')

    if input[1] == 'no':
        await state.finish()
        await bot.send_message(callback.from_user.id, messages.cancel_do, reply_markup=await keyboards.get_main_menu(callback.from_user.id))
    elif input[1] == 'yes' or input[1] == 'repeat':
        async with state.proxy() as data:
            res = await api.sendWithdrawal(callback.from_user.id, data)

            if res is None or res['success'] != 'true':
                await bot.send_message(callback.from_user.id, messages.error_do, reply_markup=await keyboards.get_main_menu(callback.from_user.id))
                await state.finish()
                return

        if input[1] != 'repeat':
            await FSMWithdrawal.next()
        await bot.send_message(callback.from_user.id, messages.withdrawal_sms, reply_markup=keyboards.markup_remove)
        aioschedule.every(10).seconds.do(withdrawal_smscode_repeat, callback.from_user.id).tag(f'smscode_repeat_{callback.from_user.id}')
    else:
        await bot.send_message(callback.from_user.id, messages.error_do)

async def withdrawal_smscode_repeat(telegram_id):
    await bot.send_message(telegram_id, messages.withdrawal_sms_repeat, reply_markup=await keyboards.withdrawal_repeat())
    aioschedule.clear(f'smscode_repeat_{telegram_id}')

async def command_withdrawal_smscode(message: types.Message, state: FSMWithdrawal.smscode):
    input = message.text

    res = await api.sendConfirmCode(message.from_user.id, input)

    if res is None or res['success'] != 'true':
        aioschedule.clear(f'smscode_repeat_{message.from_user.id}')
        await bot.send_message(message.from_user.id, messages.withdrawal_ok, reply_markup=await keyboards.get_main_menu(message.from_user.id))
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, messages.withdrawal_sms_err)


def register_handlers():
    dp.register_message_handler(check_token_cancel, commands='cancel', state='*')
    dp.register_message_handler(auth, text=[_(caption.auth, locale='en'), _(caption.auth, locale='ru')])
    dp.register_message_handler(set_token, text=[_(caption.input_token, locale='en'), _(caption.input_token, locale='ru')], state=None)
    dp.register_message_handler(without_token, text=[_(caption.run_without_token, locale='en'), _(caption.run_without_token, locale='ru')])
    dp.register_message_handler(check_token, state=FSMAdmin.token)
    # dp.register_callback_query_handler(command_withdrawal, text='withdrawal_money', state=None)
    dp.register_callback_query_handler(command_withdrawal_currency, text_contains='action_currency', state=FSMWithdrawal.currency)
    dp.register_message_handler(command_withdrawal_count, state=FSMWithdrawal.count)
    dp.register_message_handler(command_withdrawal_checkdata, state=FSMWithdrawal.pursedata)
    dp.register_callback_query_handler(command_withdrawal_choise_purse, text_contains='purse', state=FSMWithdrawal.purse)
    dp.register_callback_query_handler(command_withdrawal_confirm, text_contains='withdrawal', state=FSMWithdrawal.confirm)
    dp.register_callback_query_handler(command_withdrawal_confirm, text_contains='withdrawal:repeat', state=FSMWithdrawal.smscode)
    dp.register_message_handler(command_withdrawal_smscode, state=FSMWithdrawal.smscode)


# ======== Дополнительные функции =======
async def sendMessage(telegram_id, type, message, parse_mode=None):
    try:
        if parse_mode == types.ParseMode.HTML:
            message = re.sub(r'</?(span|p|sub|sup|blockquote|br|ol|li|ul)[^>]*>', '', message)

        if type == 'text':
            await bot.send_message(telegram_id, message, parse_mode=parse_mode)
        else:
            await bot.send_media_group(telegram_id, message)
        return [True]
    except Exception as error:
        console.printError(f"sendMessage(): {error}")
        return [False, str(error)]


async def sendMessageAll(users, type, message):
    if users is None:
        users = await database.getAllUsers()
        for user in users:
            # res = [success(bool), except(string)]
            res = await sendMessage(user['telegram_id'], type, message, types.ParseMode.HTML)

            if res[0] is False:
                return res
    else:
        for user_id in users:
            # res = [success(bool), except(string)]
            res = await sendMessage(user_id, type, message, types.ParseMode.HTML)

            if res[0] is False:
                return res

    return [True]


async def serv_generateMessage(msg_data):
    type = None
    media = []
    caption = None

    for group in msg_data:
        if group == 'message':
            caption = msg_data[group]
            type = 'text'
        else:
            for file in msg_data[group]:
                if group == 'photo':
                    media.append(types.InputMediaPhoto(file))
                elif group == 'video':
                    media.append(types.InputMediaVideo(file))
                elif group == 'document':
                    media.append(types.InputMediaDocument(file))
                elif group == 'animation':
                    media.append(types.InputMediaVideo(file))
                else:
                    console.printWarning(f"serv_generateMessage(): unknown type '{group}'")

    if len(media):
        type = 'group'
        if caption is not None:
            media[0]['caption'] = caption
        return [True, type, media]
    elif caption is not None:
        return [True, type, caption]

    return [False]


async def serv_generateMessage1(msg_data):
    type = None
    media = []
    caption = None

    for group in msg_data:
        if group == 'text':
            caption = msg_data[group]
            type = 'text'
        elif group == 'title':
            pass
        else:
            for file in msg_data[group]:
                if group == 'photo':
                    media.append(types.InputMediaPhoto(file))
                elif group == 'video':
                    media.append(types.InputMediaVideo(file))
                elif group == 'document':
                    media.append(types.InputMediaDocument(file))
                elif group == 'animation':
                    media.append(types.InputMediaVideo(file))
                else:
                    console.printWarning(f"serv_generateMessage(): unknown type '{group}'")

    if len(media):
        type = 'group'
        if caption is not None:
            media[0]['caption'] = caption
        return [True, type, media]
    elif caption is not None:
        return [True, type, caption]

    return [False]


async def serv_sendMessage(users, data):
    if data is None:
        console.printWarning('serv_sendMessage(): data is empty!')
        return [False, 'The list of messages is empty!']

    for msg in data:
        # gen_msg = [success(bool), type(string), message(InputMedia|string)]
        gen_msg = await serv_generateMessage(msg)

        if gen_msg[0] is True:
            # res = [success(bool), except(string)]
            res = await sendMessageAll(users, gen_msg[1], gen_msg[2])

            if res[0] is False:
                return res
        else:
            console.printWarning('serv_sendMessage(): message is empty!')

    return [True]

async def serv_sendNotification(data):
    if data is None:
        console.printWarning('serv_sendNotification(): data is empty!')
        return [False, 'Message is empty!']

    if 'type' not in data:
        console.printWarning('serv_sendNotification(): Unknown type of notification')
        return [False, 'Unknown type of notification!']

    try:
        if data['type'] == 'news':
            if await database.getNotigicationState(data['user'], 'news') is False:
                return [True]
        elif data['type'] == 'tickets':
            if await database.getNotigicationState(data['user'], 'tickets') is False:
                return [True]
        elif data['type'] == 'payouts':
            if await database.getNotigicationState(data['user'], 'payouts') is False:
                return [True]
        elif data['type'] == 'leads':
            if await database.getNotigicationState(data['user'], 'leads') is False:
                return [True]
        elif data['type'] != 'more':
            console.printWarning('serv_sendNotification(): Unknown type of notification')
            return [False, 'Unknown type of notification']

        text = f'''
*⚠️Уведомление: «{data['title']}»⚠️*

*{data['longtitle']}*

{data['content']}

_Дата: {data['date']}_
        '''

        if 'media' in data:
            # gen_msg = [success(bool), type(string), message(InputMedia|string)]
            gen_msg = await serv_generateMessage(data['media'])

            if gen_msg[0] is True:
                gen_msg[2][0]['caption'] = text
                gen_msg[2][0]['parse_mode'] = 'Markdown'
                res = await sendMessage(data['user'], gen_msg[1], gen_msg[2])
            else:
                console.printWarning('serv_sendNotification(): message is empty!')
        else:
            res = await sendMessage(data['user'], 'text', text, 'Markdown')

            if res[0] is False:
                return res
    except Exception as error:
        return [False, str(error)]

    return [True]
