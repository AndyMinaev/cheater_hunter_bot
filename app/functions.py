import json

from app.classes import User


def get_json_data(filename='users.json'):
    with open(filename, encoding='cp1251') as file:
        users_list = json.load(file)

    user_objects = [User(elem['id'], elem['name'], elem['team'], elem['rating'], elem['messages'],
                         elem['registration'], elem['ip'], elem['last_visited'], elem['active'])
                    for elem in users_list]

    return user_objects
