import json
import console

instructions = None


async def getInstructions():
    global instructions
    if instructions is not None:
        return instructions

    with open('./files/instructions.json') as file:
        instructions = json.load(file)

    return instructions


async def updateInstructions(data):
    global instructions
    data.pop('action')
    data.pop('token')

    if 'text' not in data:
        console.printError('updateInstructions(): There is no main text')
        return [False, 'The main text was not found!']

    # if 'data' not in data:
    #     console.printError('updateInstructions(): The instructions were not found')
    #     return [False, 'The instructions were not found!']

    try:
        if 'data' in data:
            for item_list in data['data']:
                if 'title' not in item_list:
                    console.printError('updateInstructions(): There is no title for the instructions')
                    return [False, 'There is no title for the instructions!']
                if ('text' not in item_list and not
                        ('photo' in item_list
                         or 'video' in item_list
                         or 'document' in item_list
                         or 'animation' in item_list)):
                    console.printError('updateInstructions(): There is no basic content')
                    return [False, 'There is no basic content!']

        instructions = data
        with open('./files/instructions.json', 'w') as file:
            json.dump(data, file)

    except Exception as error:
        return [False, str(error)]

    return [True]


contacts = None


async def getContacts():
    global contacts
    if contacts is not None:
        return contacts

    with open('./files/contacts.json') as file:
        contacts = json.load(file)

    return contacts


async def updateContacts(data):
    global contacts
    data.pop('action')
    data.pop('token')

    if 'text' not in data:
        console.printError('updateContacts(): There is no main text')
        return [False, 'The main text was not found!']

    try:
        if 'data' in data:
            for item_list in data['data']:
                if 'title' not in item_list:
                    console.printError('updateContacts(): There is no title for the instructions')
                    return [False, 'There is no title for the instructions!']
                if 'data' not in item_list:
                    console.printError('updateContacts(): There is no basic content')
                    return [False, 'There is no basic content!']

                for item in item_list['data']:
                    if 'text' not in item and 'media' not in item:
                        console.printError('updateContacts(): There is no basic content')
                        return [False, 'There is no basic content!']

        contacts = data
        with open('./files/contacts.json', 'w') as file:
            json.dump(data, file)

    except Exception as error:
        return [False, str(error)]

    return [True]


from googletrans import Translator


def _(text, lang):
    print(text)
    if lang == 'en':
        translator = Translator()
        text = translator.translate(text, dest='en').text
    return text
