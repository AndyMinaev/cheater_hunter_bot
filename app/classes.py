class User:
    def __init__(self, user_id, username, team, rating, messages, registration, ip, last_visited, active):
        self.id = user_id
        self.name = username
        self.team = team
        self.rating = rating
        self.messages = messages
        self.registration = registration
        self.ip = ip
        self.last_visited = last_visited
        self.active = active

    def __str__(self):
        return f'{self.name} ({self.team}), регистрация: {self.registration}, последний заход: {self.last_visited})'

    def __repr__(self):
        return f'{self.name} ({self.team}), регистрация: {self.registration}, последний заход: {self.last_visited})'