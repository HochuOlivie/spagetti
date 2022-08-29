from create_bot import _


cancel = _('/cancel - Отмена операции')
cancel_do = _('Операция отменена')
error_do = _('Проиошла ошибка')

# Вывод средств
withdrawal_balance = _('Выберите из какого счет хотите вывести средства:')
withdrawal_count = _('Выберите сумму или ее введите вручную:')
withdrawal_count_errmin = _('Сумма не может быть меньше 0')
withdrawal_count_errmax = _('Сумма не может быть больше вашего баланса!')
withdrawal_count_err = _('Введена некорректная сумма!')
withdrawal_purse = _('Укажите кошелек на который выводить средства:')
withdrawal_pursedata = _('Введите данные кошелька:')
withdrawal_sms = _('''
    На ваш телефон было отправлено сообщение с кодом подтверждения, введите этот код
    Отправка нового кода возможна через 50сек.
''').replace('    ', '')
withdrawal_sms_err = _('Код неверный, попробуйте еще раз')
withdrawal_sms_repeat = _('Если код подтверждения не пришел, можете отправить его еще раз')
withdrawal_ok = _('Запрос о выводе средств был отправлен менеджеру на обработку. Ожидайте!')

async def withdrawal_checkdata(data):
    text = _('''
        Проверьте правильность введенных данных:
        
        ---------------------------------
        Сумма: {} {}
        Кошелек: {} ({})
        ----------------------------------
        
        Подтверждаете  вывод?
    '''.format(data['count'], data['currency'], data['payment_data'], data['payment_name']).replace('    ', ''))
    return text

async def withdrawal_willpay(count, currency):
    return _("С вашего кашелька будет списано {} {}".format(count, currency))

async def withdrawal_purse_invalid(example):
    exc = ''

    if example is not None:
        exc = _('Напишите номер кошелька в формате: *{}*'.format(example))

    text = _('''
    Введен некорректный номер кошелька!
    {}
    '''.format(exc).replace('    ', ''))
    return text