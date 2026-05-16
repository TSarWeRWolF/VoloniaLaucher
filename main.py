import os
import time
import json
import hashlib
import random
import platform
import shutil
from datetime import datetime, timezone
from collections import defaultdict, deque
import threading

# =========================
# CONFIGURATION
# =========================

CONFIG = {
    "watched_dir": "./secure_folder",
    "log_file": "security_log.json",
    "hash_db": "file_hashes.json",
    "quarantine_dir": "./quarantine",
    "scan_interval": 5,
    "scan_threshold": 12,
    "report_file": "report.html"
}

# Глобальные локи для потокобезопасности
log_lock = threading.Lock()
hash_db_lock = threading.Lock()


# =========================
# EVENT SYSTEM
# =========================

class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type, callback):
        with self._lock:
            self._listeners[event_type].append(callback)

    def emit(self, event_type, data):
        # Копируем список, чтобы избежать race condition при изменении подписчиков во время рассылки
        with self._lock:
            current_listeners = list(self._listeners[event_type])
        for callback in current_listeners:
            try:
                callback(data)
            except Exception as e:
                print(f"[EVENT_BUS_ERROR] Error in callback: {e}")


bus = EventBus()


# =========================
# LOGGER
# =========================

def now():
    return datetime.now(timezone.utc).isoformat()


def write_log(event_type, message, severity="INFO"):
    entry = {
        "time": now(),
        "type": event_type,
        "severity": severity,
        "message": message
    }

    # Потокобезопасная запись в файл логов
    with log_lock:
        logs = []
        if os.path.exists(CONFIG["log_file"]):
            try:
                with open(CONFIG["log_file"], "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                # Если файл поврежден, бэкапим его и создаем чистый
                os.rename(CONFIG["log_file"], f"{CONFIG['log_file']}.corrupt")
                logs = []
            except Exception as e:
                print(f"[LOGGER_ERROR] Cannot read log file: {e}")

        logs.append(entry)

        try:
            with open(CONFIG["log_file"], "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4)
        except Exception as e:
            print(f"[LOGGER_ERROR] Cannot write log file: {e}")

    print(f"[{severity}] {event_type} -> {message}")
    bus.emit(event_type, entry)


# =========================
# FILE HASHING
# =========================

def sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, PermissionError) as e:
        write_log("HASH_ERROR", f"Permission denied or file missing: {path} ({str(e)})", "ERROR")
        return None


# =========================
# QUARANTINE SYSTEM
# =========================

class QuarantineManager:
    def __init__(self, folder):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def quarantine(self, file_path):
        if not os.path.exists(file_path):
            return

        name = os.path.basename(file_path)
        # Добавляем таймстэмп к имени, чтобы избежать коллизий, если файлы называются одинаково
        timestamp = int(time.time())
        target = os.path.join(self.folder, f"{timestamp}_{name}")

        try:
            shutil.move(file_path, target)
            write_log("QUARANTINE", f"Moved {file_path} -> {target}", "CRITICAL")
        except Exception as e:
            write_log("QUARANTINE_ERROR", f"Failed to quarantine {file_path}: {str(e)}", "ERROR")


quarantine_manager = QuarantineManager(CONFIG["quarantine_dir"])


# =========================
# FILE INTEGRITY MONITOR
# =========================

class IntegrityMonitor:
    def __init__(self, folder):
        self.folder = folder
        self.hash_db = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG["hash_db"]):
            with hash_db_lock:
                try:
                    with open(CONFIG["hash_db"], "r", encoding="utf-8") as f:
                        self.hash_db = json.load(f)
                except Exception as e:
                    write_log("DB_ERROR", f"Failed to load hash DB: {str(e)}", "ERROR")

    def save(self):
        with hash_db_lock:
            try:
                with open(CONFIG["hash_db"], "w", encoding="utf-8") as f:
                    json.dump(self.hash_db, f, indent=4)
            except Exception as e:
                write_log("DB_ERROR", f"Failed to save hash DB: {str(e)}", "ERROR")

    def scan(self):
        is_dirty = False
        scanned_paths = set()

        for root, _, files in os.walk(self.folder):
            for file in files:
                path = os.path.join(root, file)
                scanned_paths.add(path)
                h = sha256(path)
                if not h:
                    continue

                if path not in self.hash_db:
                    self.hash_db[path] = h
                    write_log("FILE_NEW", path)
                    is_dirty = True
                elif self.hash_db[path] != h:
                    write_log("FILE_TAMPERED", path, "WARNING")
                    # Вместо прямого вызова карантина генерируем событие!
                    bus.emit("INCIDENT_TAMPERED", {"path": path})
                    self.hash_db[path] = h
                    is_dirty = True

        # Проверка на удаленные файлы
        deleted_files = set(self.hash_db.keys()) - scanned_paths
        for path in deleted_files:
            del self.hash_db[path]
            write_log("FILE_DELETED", path, "WARNING")
            is_dirty = True

        # Сохраняем ТОЛЬКО если были изменения
        if is_dirty:
            self.save()


# =========================
# NETWORK IDS
# =========================

class NetworkMonitor:
    def __init__(self):
        self.connections = defaultdict(deque)
        self._lock = threading.Lock()

    def add_connection(self, ip):
        t = time.time()
        with self._lock:
            self.connections[ip].append(t)
            # Очистка старых записей (> 60 сек)
            while self.connections[ip] and t - self.connections[ip][0] > 60:
                self.connections[ip].popleft()

            count = len(self.connections[ip])

        if count > CONFIG["scan_threshold"]:
            write_log("PORT_SCAN", f"IP: {ip} executed {count} requests in 60s", "CRITICAL")


# =========================
# RULE ENGINE
# =========================

class RuleEngine:
    def __init__(self):
        self.rules = []

    def add_rule(self, name, condition, action):
        self.rules.append((name, condition, action))

    def evaluate(self, event_type, data):
        # Адаптируем под работу с шиной событий
        event_packet = {"type": event_type, **data}
        for name, condition, action in self.rules:
            try:
                if condition(event_packet):
                    action(event_packet)
            except Exception as e:
                print(f"[RULE_ERROR] Rule '{name}' failed: {e}")


engine = RuleEngine()

# Реализация правил через слабую связанность событий
engine.add_rule(
    "critical_alert_print",
    lambda e: e.get("severity") == "CRITICAL",
    lambda e: print(f"\n[!!! SIEM ALERT !!!] Critical event registered: {e.get('message')}\n")
)

engine.add_rule(
    "auto_quarantine_on_tamper",
    lambda e: e.get("type") == "INCIDENT_TAMPERED",
    lambda e: quarantine_manager.quarantine(e.get("path"))
)

# Подписываем Rule Engine на все основные типы событий
bus.subscribe("FILE_TAMPERED", lambda data: engine.evaluate("FILE_TAMPERED", data))
bus.subscribe("PORT_SCAN", lambda data: engine.evaluate("PORT_SCAN", data))
bus.subscribe("INCIDENT_TAMPERED", lambda data: engine.evaluate("INCIDENT_TAMPERED", data))


# =========================
# SYSTEM INFO
# =========================

def get_system_info():
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine()
    }


# =========================
# REPORT GENERATOR
# =========================

class ReportGenerator:
    def generate(self):
        if not os.path.exists(CONFIG["log_file"]):
            return

        with log_lock:
            try:
                with open(CONFIG["log_file"], "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                return

        stats = defaultdict(int)
        for log in logs:
            stats[log["type"]] += 1

        # Верстка базового, но чистого HTML-отчета
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cyber Defense Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; background-color: #f4f6f9; color: #333; }}
        h1, h2 {{ color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ background: #fff; margin: 5px 0; padding: 10px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .badge {{ font-weight: bold; color: #e74c3c; }}
    </style>
</head>
<body>
    <h1>Security System Report</h1>
    <h2>System Information</h2>
    <pre>{json.dumps(get_system_info(), indent=2)}</pre>
    <h2>Event Metrics</h2>
    <ul>
"""
        for k, v in stats.items():
            html += f"        <li><strong>{k}:</strong> <span class='badge'>{v}</span> incidents</li>\n"

        html += """    </ul>
</body>
</html>"""

        try:
            with open(CONFIG["report_file"], "w", encoding="utf-8") as f:
                f.write(html)
            print("[REPORT] HTML report updated successfully.")
        except Exception as e:
            print(f"[REPORT_ERROR] Failed to write HTML report: {e}")


reporter = ReportGenerator()


# =========================
# SIMULATED TRAFFIC
# =========================

class FakeTraffic:
    def __init__(self, net):
        self.net = net
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        fake_ips = ["192.168.0.10", "10.0.0.5", "172.16.0.3", "8.8.8.8"]
        while self.running:
            # Используем random вместо привязки к жесткому времени, чтобы симуляция была живой
            ip = random.choice(fake_ips)
            self.net.add_connection(ip)
            # Случайная частота запросов для симуляции реального сканирования
            time.sleep(random.uniform(0.1, 0.6))


# =========================
# MAIN SYSTEM
# =========================

class CyberDefenseSystem:
    def __init__(self):
        self.integrity = IntegrityMonitor(CONFIG["watched_dir"])
        self.network = NetworkMonitor()
        self.traffic = FakeTraffic(self.network)
        self.running = False

    def start(self):
        self.running = True
        write_log("SYSTEM_START", "Cyber Defense System initialized successfully.", "INFO")

        threading.Thread(target=self.loop_integrity, daemon=True).start()
        self.traffic.start()
        threading.Thread(target=self.loop_report, daemon=True).start()

        print("[SYSTEM] System is running. Press Ctrl+C to terminate.")
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("\n[SYSTEM] Shutting down gracefully...")
        self.running = False
        self.traffic.stop()
        write_log("SYSTEM_STOP", "Cyber Defense System stopped.", "INFO")
        time.sleep(1)  # Время для завершения записи логов

    def loop_integrity(self):
        while self.running:
            self.integrity.scan()
            # Дробим sleep на мелкие части, чтобы поток мгновенно реагировал на self.running = False
            for _ in range(CONFIG["scan_interval"]):
                if not self.running: break
                time.sleep(1)

    def loop_report(self):
        while self.running:
            for _ in range(20):
                if not self.running: break
                time.sleep(1)
            if self.running:
                reporter.generate()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    os.makedirs(CONFIG["watched_dir"], exist_ok=True)
    os.makedirs(CONFIG["quarantine_dir"], exist_ok=True)

    system = CyberDefenseSystem()
    system.start()

