import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import warnings
warnings.filterwarnings("ignore")


def get_users_list(url):
    base_url = 'https://pefl.ru/'

    r = session.get(url)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'html.parser')

    a_items = soup.find_all('a')
    user_links = [f"{base_url}{link.get('href')}" for link in a_items if
                  link.get('href').startswith('users.php') and link.text in active_users]
    user_links = user_links[1:]

    return user_links


def parse_user(url):
    r = session.get(url, headers=header)
    r.encoding = r.apparent_encoding
    tables = pd.read_html(r.text)

    if len(tables[-1]) >= 27:
        table = tables[-1]
    else:
        table = tables[-2]

    soup = BeautifulSoup(r.text)
    a_items = soup.find_all('a')
    link = [f"https://pefl.ru/{tag.get('href')}" for tag in a_items if tag.text == 'Правка']

    user_id = int(url.split('=')[-1])
    name = table.loc[1][1]

    if table.loc[3][1] is np.nan:
        team = ''
    else:
        team = table.loc[3][1].split(' | ')[0]

    rating = table.loc[6][1]
    messages = int(table.loc[12][1].split()[0])
    registered = table.loc[24][1]

    ip, last_visited = '', ''
    if link:
        link = link[0]
        r = session.get(link, headers=header)
        r.encoding = r.apparent_encoding
        tables = pd.read_html(r.text)

        try:
            table_content = tables[-2].loc[0][1]
            index_1 = table_content.find('Последний вход в систему :  ')
            index_2 = table_content.find('Последний известный IP :  ')
            index_3 = table_content.find('Счетчик ')
            last_visited = table_content[index_1 + 28 : index_2 - 2]
            ip = table_content[index_2 + 26 : index_3 - 2]
        except:
            pass

    return user_id, name, team, rating, messages, registered, ip, last_visited


login = input('Введи свой логин: ')
password = input('Введи свой пароль: ')

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
host = 'https://pefl.ru/'
link = 'https://pefl.ru/auth.php?m=login&a=check'

data = {
    'rusername': login,
    'rpassword': password
}

session = requests.Session()
response = session.post(link, data=data, headers=header).text


ratings_url = 'https://pefl.ru/plug.php?p=rating&t=m&z=099659e4f129319d04d4927f4076547c'
r = session.get(ratings_url)
r.encoding = r.apparent_encoding

try:
    print('Собираю список менеджеров с командами... Это займет несколько минут...')
    ratings = pd.read_html(r.text)
    ratings = ratings[-1]
    ratings = ratings.loc[3:]
    ratings_active = ratings.dropna()
    active_users = list(ratings_active[1])
except Exception as err:
    print(f'Не смог получить список менеджеров: {err}')
    input('Нажми любую клавишу, чтобы закончить...')

# формируем файл, содержащий ссылки на менеджеров с командами
users_links = get_users_list(ratings_url)
with open('users_links.txt', 'w') as file:
    for line in users_links:
        file.write(f'{line}\n')

print('Файл со списком менеджеров сформирован!')
print('Начинаю парсить аккаунты менеджеров...')

cols = ['id', 'name', 'team', 'rating', 'messages', 'registration', 'ip', 'last_visited']
data = pd.DataFrame(columns=cols)
count = 0

for link in users_links:
    try:
        data.loc[count] = parse_user(link)
    except Exception as e:
        print(f'Не удалось спарсить менеджера по ссылке {link}, \nОшибка: {e}')
    count += 1
    print(f'{count} / {len(users_links)} обработано')

print('Парсинг менеджеров завершен. Сохраняю файлы')
data.to_excel('users.xlsx', index=False)
data.to_json('users.json', orient='records', indent=4, force_ascii=False)

print('Файлы сохранены')
input('Нажми любую клавишу, чтобы закрыть окно...')
