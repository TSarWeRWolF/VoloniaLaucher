import tkinter as tk
import subprocess
import webbrowser
import random

root = tk.Tk()
root.geometry("700x450")
root.configure(bg="black")
root.title("VOLON OS v1.1")

FONT = ("Consolas", 11)

# ===== BOOT =====
boot_label = tk.Label(root, text="", fg="lime", bg="black", font=FONT, justify="left")
boot_label.pack(anchor="w", padx=10, pady=10)

boot_text = [
    "VOLON OS v1.1",
    "Booting system...",
    "Loading kernel...",
    "Connecting to network...",
    "Security modules: OK",
    "System ready."
]

def type_text(text, widget, i=0):
    if i < len(text):
        widget.config(text=widget.cget("text") + text[i])
        root.after(20, type_text, text, widget, i+1)

def boot_sequence(i=0):
    if i < len(boot_text):
        type_text(boot_text[i] + "\n", boot_label)
        root.after(800, boot_sequence, i+1)
    else:
        root.after(500, show_menu)

# ===== MENU =====
menu_frame = tk.Frame(root, bg="black")

def show_menu():
    boot_label.pack_forget()
    menu_frame.pack(expand=True)

    tk.Label(menu_frame, text="== VOLON OS ==", fg="lime", bg="black", font=("Consolas", 16)).pack(pady=10)

    create_btn("🎮 Games", open_games)
    create_btn("💻 Terminal", open_terminal)
    create_btn("🌐 Browser", open_browser)

def create_btn(text, cmd):
    btn = tk.Button(menu_frame, text=text, width=25, command=cmd,
                    bg="black", fg="lime", activebackground="black", activeforeground="white")
    btn.pack(pady=5)

def clear():
    for w in menu_frame.winfo_children():
        w.destroy()

def back():
    clear()
    show_menu()

# ===== GAMES =====
def open_games():
    clear()
    tk.Label(menu_frame, text="Games module", fg="lime", bg="black", font=FONT).pack()

    create_btn("Run Minecraft", run_minecraft)
    create_btn("⬅ Back", back)

def run_minecraft():
    try:
        subprocess.Popen([
            "/home/a/Загрузки/Minecraft (2)/minecraft-launcher"
        ])
    except Exception as e:
        print("Ошибка запуска:", e)

# ===== TERMINAL =====
def open_terminal():
    clear()

    terminal = tk.Text(menu_frame, bg="black", fg="lime", insertbackground="lime", font=FONT)
    terminal.pack(fill="both", expand=True)

    terminal.insert("end", "VOLON TERMINAL\nType 'help'\n\n> ")
    terminal.focus()

    def execute(event):
        cmd = terminal.get("end-2l linestart", "end-1c").replace("> ", "").strip()

        terminal.insert("end", "\n")

        if cmd == "help":
            type_out("Commands: help, scan, hack, clear\n", terminal)
        elif cmd == "scan":
            fake_scan(terminal)
        elif cmd == "hack":
            fake_hack(terminal)
        elif cmd == "clear":
            terminal.delete("1.0", "end")
        else:
            type_out("Unknown command\n", terminal)

        terminal.insert("end", "\n> ")
        terminal.see("end")

    terminal.bind("<Return>", execute)

def type_out(text, widget, i=0):
    if i < len(text):
        widget.insert("end", text[i])
        widget.see("end")
        root.after(10, type_out, text, widget, i+1)

def fake_scan(widget):
    lines = [
        "Scanning network...",
        "IP found: 192.168.0." + str(random.randint(2, 255)),
        "Checking ports...",
        "Vulnerability detected!",
        "Scan complete."
    ]
    animate_lines(widget, lines)

def fake_hack(widget):
    lines = [
        "Connecting to target...",
        "Bypassing firewall...",
        "Injecting payload...",
        "ACCESS GRANTED",
        "Downloading data..."
    ]
    animate_lines(widget, lines)

def animate_lines(widget, lines, i=0):
    if i < len(lines):
        type_out(lines[i] + "\n", widget)
        root.after(400, animate_lines, widget, lines, i+1)

# ===== BROWSER =====
def open_browser():
    clear()
    tk.Label(menu_frame, text="Browser module", fg="lime", bg="black").pack()

    create_btn("Open site", lambda: webbrowser.open("https://anihub.in.ua/"))
    create_btn("⬅ Back", back)

# ===== START =====
boot_sequence()
root.mainloop()