import json
import os


class DataManager:
    def __init__(self, filename="users.json"):
        self.filename = filename
        self.ensure_file()

    def ensure_file(self):
        """Создает файл если его нет или он пустой"""
        if not os.path.exists(self.filename) or os.stat(self.filename).st_size == 0:
            with open(self.filename, "w") as f:
                json.dump({"users": []}, f)

    def load_users(self):
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
                return data.get("users", [])
        except json.JSONDecodeError:
            return []

    def save_users(self, users):
        with open(self.filename, "w") as f:
            json.dump({"users": users}, f, indent=4)

    def get_user(self, username):
        print("INPUT:", repr(username))

        for user in self.load_users():
            print("DB:", repr(user["username"]))

            if user["username"] == username:
                return user
        return None