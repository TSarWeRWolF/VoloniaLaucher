import tkinter as tk
from tkinter import messagebox


class AppUI:
    def __init__(self, root, security):
        self.root = root
        self.security = security

        self.root.title("Secure Launcher")
        self.root.geometry("400x300")

        self.create_frames()
        self.show_frame(self.login_frame)

    def create_frames(self):
        self.login_frame = tk.Frame(self.root)
        self.guard_frame = tk.Frame(self.root)
        self.main_frame = tk.Frame(self.root)

        self.build_login()
        self.build_guard()
        self.build_main()

    def show_frame(self, frame):
        for f in (self.login_frame, self.guard_frame, self.main_frame):
            f.pack_forget()
        frame.pack(fill="both", expand=True)

    # --- LOGIN ---
    def build_login(self):
        tk.Label(self.login_frame, text="Login").pack(pady=10)

        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack()

        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.pack()

        tk.Button(self.login_frame, text="Увійти", command=self.handle_login).pack(pady=10)

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        success, msg = self.security.login(username, password)

        if success:
            self.show_frame(self.guard_frame)
        else:
            messagebox.showerror("Помилка", msg)

    # --- GUARD ---
    def build_guard(self):
        tk.Label(self.guard_frame, text="Введіть код").pack(pady=10)

        self.code_entry = tk.Entry(self.guard_frame)
        self.code_entry.pack()

        tk.Button(self.guard_frame, text="Підтвердити", command=self.check_code).pack(pady=10)

    def check_code(self):
        code = self.code_entry.get()

        if self.security.verify_code(code):
            self.show_frame(self.main_frame)
        else:
            messagebox.showerror("Помилка", "Невірний код")

    # --- MAIN ---
    def build_main(self):
        tk.Label(self.main_frame, text="Лаунчер").pack(pady=20)

        tk.Button(self.main_frame, text="Запустити гру", command=self.run_game).pack(pady=5)
        tk.Button(self.main_frame, text="Вийти", command=self.logout).pack(pady=5)

    def run_game(self):
        messagebox.showinfo("Game", "Гра запущена 🚀")

    def logout(self):
        self.show_frame(self.login_frame)