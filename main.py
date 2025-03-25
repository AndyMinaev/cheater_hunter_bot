import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile

import json
import pandas as pd

from dotenv import load_dotenv
from app.functions import get_json_data


# загружаем данные пользователей из json-файла
users = get_json_data()
print('ready to go')

# запускаем бота
load_dotenv()
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Введи имя менеджера, чтобы найти пересечения по IP с другими менеджерами '
                         'или проверь, какие менеджеры заходили с конкретного IP-адреса.\n\n'
                         'Подробнее о том, как пользоваться ботом - по команде /help')


@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Чтобы проверить менеджера, просто введи его имя (регистр не важен).\n\n'
                         'Чтобы найти менеджеров, которые заходили с конкретного IP адреса, отправь сообщение '
                         'в формате IP xxx.xxx.xxx.xxx.\n\n'
                         'Чтобы обновить данные, отправь пользователю JSON-файл, сформированный парсером.\n\n'
                         'Чтобы скачать excel-файл с информацией по менеджерам, используй команду /get_excel.\n\n'
                         'Что скачать JSON-файл с информацией по менеджерам, используй команду /get_json.\n\n')


@dp.message(Command(commands=['get_excel']))
async def get_excel(message: Message):
    await message.answer('Выгружаю данные в Excel...')
    attrs = ['id', 'name', 'team', 'rating', 'messages', 'registration', 'ip', 'last_visited', 'active']
    excel_data = pd.DataFrame(columns=attrs)

    for user in users:
        for ip in user.ip:
            excel_data.loc[len(excel_data)] = [user.id, user.name, user.team, user.rating, user.messages,
                                               user.registration, ip, user.last_visited, user.active]

    try:
        excel_data.to_excel('users.xlsx', index=False)
        await message.answer('Файл готов, отправляю...')
        await message.answer_document(FSInputFile('users.xlsx'))
    except Exception as e:
        await message.answer(f'Не удалось отправить файл: {e}')


@dp.message(Command(commands=['get_json']))
async def get_json(message: Message):
    await message.answer('Выгружаю JSON...')
    await message.answer_document((FSInputFile('users.json')))


@dp.message(F.document)
async def update(message: Message):
    global users
    file_id = message.document.file_id
    await Bot.download(bot, file_id, 'users_parsed.json')
    await message.answer('Обновляю данные...')

    # создаем словарь пользователей на основе существующей БД
    users_dict = {user.id: {
        "id": user.id,
        "name": user.name,
        "team": user.team,
        "rating": user.rating,
        "messages": user.messages,
        "registration": user.registration,
        "ip": user.ip,
        "last_visited": user.last_visited,
        "active": user.active
    } for user in users}

    # создаем словарь из полученных данных
    with open('users_parsed.json', encoding='utf-8') as file:
        new_data = json.load(file)
    attrs = ['id', 'name', 'team', 'rating', 'messages', 'registration', 'ip', 'last_visited']
    new_users_dict = {str(elem['id']): {attr: elem[attr] for attr in attrs} for elem in new_data}

    # переносим данные из словаря с апдейтом в словарь существующих данных
    for uid in new_users_dict:
        if uid in users_dict:
            old_user, new_user = users_dict[uid], new_users_dict[uid]
            if not old_user['team']:
                old_user['active'] = True
            old_user['team'] = new_user['team']
            old_user['rating'] = new_user['rating']
            old_user['messages'] = new_user['messages']
            old_user['last_visited'] = new_user['last_visited']

            if new_user['ip'] not in old_user['ip']:
                old_user['ip'].append(new_user['ip'])
        else:
            new_user = new_users_dict[uid]
            users_dict[uid] = {
                'id': new_user['id'],
                'name': new_user['name'],
                'team': new_user['team'],
                'rating': new_user['rating'],
                'messages': new_user['messages'],
                'registration': new_user['registration'],
                'ip': list(new_user['ip']),
                'last_visited': new_user['last_visited'],
                'active': True
            }

    # убираем из словаря существующих данных команды тем пользователям, кого нет в апдейте
    non_team_ids = [uid for uid in users_dict if uid not in new_users_dict]
    for uid in non_team_ids:
        users_dict[uid]['team'] = ''
        users_dict[uid]['active'] = False

    # сохраняем обновленные данные в users.json
    data_to_json = [users_dict[uid] for uid in users_dict]
    with open('test.json', 'w', encoding='cp1251') as file:
        json.dump(data_to_json, file, ensure_ascii=False, indent=4)

    # обновляем список users
    users = get_json_data()
    await message.answer('Данные обновлены!')


@dp.message()
async def any_message(message: Message):
    if message.text.lower().startswith('ip '):
        await message.answer('Проверяю IP...')
        ip_to_check = message.text[3:]
        users_with_ip = [user for user in users if ip_to_check in user.ip]

        if users_with_ip:
            users_with_ip.sort(key=lambda x: x.last_visited)
            for user in users_with_ip:
                await message.answer(
                    f'{user.name} ({user.team}),\nРегистрация: {user.registration},\nПоследний заход: {user.last_visited})')
        else:
            await message.answer('Нет менеджеров с таким IP')

    else:
        user_to_check = [user for user in users if user.name.lower() == message.text.lower()]
        if user_to_check:
            user_to_check = user_to_check[0]
            ip_to_check = user_to_check.ip

            for ip in ip_to_check:
                await message.answer(f'Проверяю IP-адрес {ip}:')
                clones = [user for user in users if ip in user.ip and user_to_check.name.lower() != user.name.lower()]

                if clones:
                    clones.sort(key=lambda x: x.last_visited)
                    for user in clones:
                        await message.answer(
                            f'{user.name} ({user.team}),\nРегистрация: {user.registration},'
                            f'\nПоследний заход: {user.last_visited})')
                else:
                    await message.answer('Нет совпадений по этому IP\n')
        else:
            await message.answer('Менеджера с таким именем не существует')


if __name__ == '__main__':
    dp.run_polling(bot)
