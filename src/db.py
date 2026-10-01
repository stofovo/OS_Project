import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'os.sqlite')

def get_connection():
    """Возвращает соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создает структуру таблиц учебной ОС."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL
    )
    ''')
    
    # Таблица процессов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processes (
        pid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        owner_id INTEGER NOT NULL,
        memory_kb INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id)
    )
    ''')
    
    # Таблица файлов (имитация файловой системы)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        content TEXT,
        owner_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id)
    )
    ''')
    
    # Журнал системных вызовов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS syscalls_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        args TEXT,
        user TEXT,
        status TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    
    # Создаем дефолтного администратора (пароль: admin)
    import hashlib
    admin_hash = hashlib.sha256(b'admin').hexdigest()
    cursor.execute('INSERT OR IGNORE INTO users (login, password_hash, role, created_at) VALUES (?, ?, ?, ?)', 
                   ('admin', admin_hash, 'admin', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("База данных инициализирована. Файл os.sqlite создан в папке db.")