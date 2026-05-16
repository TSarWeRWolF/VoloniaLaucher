import hashlib


class SecurityManager:
    def __init__(self, data_manager):
        self.data = data_manager
        self.current_user = None

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        user = self.data.get_user(username)

        if not user:
            return False, "Користувача не знайдено"

        if user["password"] != password:
            return False, "Невірний пароль"

        self.current_user = user
        return True, "OK"

    def verify_code(self, code):
        if code == self.current_user["guard_code"]:
            return True
        return False