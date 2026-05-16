import os
import tkinter as tk
import minecraft_launcher_lib

# папка где будет minecraft
MC_DIR = os.path.expanduser("~/.volon_minecraft")

# ===== GUI =====
root = tk.Tk()
root.title("Volon Launcher")
root.geometry("400x300")
root.configure(bg="black")

FONT = ("Consolas", 11)

# ===== NICK =====
tk.Label(root, text="Nickname:", fg="lime", bg="black", font=FONT).pack()
nickname_entry = tk.Entry(root)
nickname_entry.pack()

# ===== VERSION =====
tk.Label(root, text="Version:", fg="lime", bg="black", font=FONT).pack()
version_var = tk.StringVar(value="1.20.1")

versions = ["1.20.1", "1.19.4", "1.18.2"]
for v in versions:
    tk.Radiobutton(root, text=v, variable=version_var,
                   value=v, bg="black", fg="lime",
                   selectcolor="black").pack()

# ===== STATUS =====
status_label = tk.Label(root, text="", fg="lime", bg="black")
status_label.pack(pady=10)

# ===== INSTALL =====
def install():
    version = version_var.get()
    status_label.config(text=f"Installing {version}...")

    minecraft_launcher_lib.install.install_minecraft_version(version, MC_DIR)

    status_label.config(text="Install complete")

# ===== LAUNCH =====
def launch():
    version = version_var.get()
    nickname = nickname_entry.get()

    if nickname == "":
        status_label.config(text="Enter nickname!")
        return

    options = {
        "username": nickname,
        "uuid": "12345678-1234-5678-1234-567812345678",
        "token": "",
    }

    command = minecraft_launcher_lib.command.get_minecraft_command(
        version,
        MC_DIR,
        options
    )

    status_label.config(text="Launching...")
    os.system(" ".join(command))

# ===== BUTTONS =====
tk.Button(root, text="Install", command=install).pack(pady=5)
tk.Button(root, text="Play", command=launch).pack(pady=5)

root.mainloop()