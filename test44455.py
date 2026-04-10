import tkinter as tk
from tkinter import messagebox
import cv2
import face_recognition
import bcrypt
import os

# =========================
# 🔐 БАЗА ДАНИХ (локальна)
# =========================
USER_FILE = "user_face.jpg"
PASSWORD_HASH = None

# =========================
# 🔐 ХЕШУВАННЯ ПАРОЛЯ
# =========================
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed)

# =========================
# 📷 РЕЄСТРАЦІЯ ОБЛИЧЧЯ
# =========================
def register_face():
    video = cv2.VideoCapture(0)
    messagebox.showinfo("Інструкція", "Натисни 'S' щоб зберегти обличчя")

    while True:
        ret, frame = video.read()
        cv2.imshow("Реєстрація", frame)

        key = cv2.waitKey(1)

        if key == ord('s'):
            cv2.imwrite(USER_FILE, frame)
            messagebox.showinfo("OK", "Обличчя збережено!")
            break
        elif key == 27:
            break

    video.release()
    cv2.destroyAllWindows()

# =========================
# 🤖 FACE ID ВХІД
# =========================
def face_login():
    if not os.path.exists(USER_FILE):
        messagebox.showerror("Помилка", "Спочатку зареєструй обличчя!")
        return False

    known_image = face_recognition.load_image_file(USER_FILE)
    known_encoding = face_recognition.face_encodings(known_image)[0]

    video = cv2.VideoCapture(0)

    while True:
        ret, frame = video.read()
        rgb = frame[:, :, ::-1]

        encodings = face_recognition.face_encodings(rgb)

        for face in encodings:
            match = face_recognition.compare_faces([known_encoding], face)
            if match[0]:
                video.release()
                cv2.destroyAllWindows()
                return True

        cv2.imshow("Face ID", frame)

        if cv2.waitKey(1) == 27:
            break

    video.release()
    cv2.destroyAllWindows()
    return False

# =========================
# 🔐 РЕЄСТРАЦІЯ
# =========================
def register():
    global PASSWORD_HASH
    password = entry_password.get()

    if not password:
        messagebox.showerror("Помилка", "Введи пароль!")
        return

    PASSWORD_HASH = hash_password(password)
    register_face()
    messagebox.showinfo("OK", "Реєстрація завершена!")

# =========================
# 🔐 ВХІД
# =========================
def login():
    password = entry_password.get()

    if PASSWORD_HASH is None:
        messagebox.showerror("Помилка", "Спочатку зареєструйся!")
        return

    if not check_password(password, PASSWORD_HASH):
        messagebox.showerror("Помилка", "Невірний пароль!")
        return

    if face_login():
        open_launcher()
    else:
        messagebox.showerror("Помилка", "Face ID не підтверджено!")

# =========================
# 🎮 ЛАУНЧЕР (типо Steam)
# =========================
def open_launcher():
    launcher = tk.Toplevel(root)
    launcher.title("Game Launcher")
    launcher.geometry("400x300")

    tk.Label(launcher, text="🎮 Мої ігри", font=("Arial", 16)).pack(pady=10)

    tk.Button(launcher, text="Запустити Minecraft", command=lambda: print("Запуск гри")).pack(pady=5)
    tk.Button(launcher, text="Запустити CS2", command=lambda: print("Запуск гри")).pack(pady=5)

# =========================
# 🖥️ GUI
# =========================
root = tk.Tk()
root.title("Secure Launcher")
root.geometry("300x250")

tk.Label(root, text="Пароль:").pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Реєстрація", command=register).pack(pady=5)
tk.Button(root, text="Вхід (Face ID)", command=login).pack(pady=5)

root.mainloop()