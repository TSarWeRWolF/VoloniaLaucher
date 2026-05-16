import tkinter as tk
import os

print("hello user")
input("press enter to start")

# ===== ROOT =====
root = tk.Tk()
root.title("gamebook")
root.geometry("400x400")
root.resizable(False, False)
root.configure(bg="#ffffff")

# ===== MAIN MENU =====
class MainMenu(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.configure(bg="#ffffff")
        self.pack(fill="both", expand=True)

        self.title = tk.Label(
            self,
            text="GAMEBOOK",
            font=("Arial", 20),
            bg="#ffffff"
        )
        self.title.pack(pady=20)

        self.play_button = MyButton(
            self,
            text="PLAY"
        )
        self.play_button.pack(pady=10)

# ===== CUSTOM BUTTON =====
class MyButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(
            width=20,
            height=2,
            bg="#222222",
            fg="white"
        )

# ===== START =====
main_menu = MainMenu(root)

root.mainloop()


