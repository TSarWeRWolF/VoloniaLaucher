import tkinter as tk
from data import DataManager
from security import SecurityManager
from ui import AppUI


def main():
    root = tk.Tk()

    data = DataManager()
    security = SecurityManager(data)

    app = AppUI(root, security)

    root.mainloop()


if __name__ == "__main__":
    main()

