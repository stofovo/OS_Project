from src.db import get_connection, THIS_DIR
import json
import hashlib

# Глобальная переменная текущего пользователя
CURRENT_USER = None

def log_syscall(name: str, args=None, status="success"):
    """
    Логирует системный вызов в таблицу syscalls_log.
    Args:
        name: Имя вызова.
        args: Словарь аргументов.
        status: Статус выполнения ("success", "failure").
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO syscalls_log (syscall_name, args, user, status) VALUES (?, ?, ?, ?)",
                  [name, json.dumps(args), CURRENT_USER or "guest", status])
    conn.commit()

# ====== СИСТЕМНЫЕ ВЫЗОВЫ ======

def sys_login(login: str, password: str):
    global CURRENT_USER
    conn = get_connection()
    cursor = conn.cursor()

    # Проверяем существование пользователя
    cursor.execute("SELECT password_hash FROM users WHERE login=?", [login])
    row = cursor.fetchone()
    if not row:
        log_syscall("sys_login", {"login": login}, "failure")
        return False

    # Проверка хэша пароля
    hashed_input = hashlib.sha256(password.encode()).hexdigest()
    if hashed_input != row[0]:
        log_syscall("sys_login", {"login": login}, "failure")
        return False

    # Успешная авторизация
    CURRENT_USER = login
    log_syscall("sys_login", {"login": login})
    return True

def sys_logout():
    global CURRENT_USER
    old_user = CURRENT_USER
    CURRENT_USER = None
    log_syscall("sys_logout", {"old_user": old_user})
    return None

def sys_whoami():
    log_syscall("sys_whoami")
    return CURRENT_USER or "guest"

def sys_create_file(path: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()

    # Заглушка проверки прав доступа
    if CURRENT_USER is None:
        log_syscall("sys_create_file", {"path": path}, "failure")
        return None

    # Создаем файл в БД
    cursor.execute("INSERT INTO files (path, content, owner_id) SELECT ?, ?, u.id "
                   "FROM users AS u WHERE u.login=?",
                   [path, content[:100], CURRENT_USER])  # Берём только первые 100 символов контента
    file_id = cursor.lastrowid
    conn.commit()

    log_syscall("sys_create_file", {"path": path})
    return file_id

def sys_read_file(fid: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем владельца файла
    cursor.execute("SELECT f.content, u.login FROM files AS f JOIN users AS u ON f.owner_id=u.id WHERE f.fid=?",
                   [fid])
    row = cursor.fetchone()

    # Если пользователь не авторизован или это чужой файл
    if not row or (CURRENT_USER and row[1] != CURRENT_USER):
        log_syscall("sys_read_file", {"fid": fid}, "failure")
        return None

    log_syscall("sys_read_file", {"fid": fid})
    return row[0]

def sys_delete_file(fid: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем владельца файла
    cursor.execute("SELECT u.login FROM files AS f JOIN users AS u ON f.owner_id=u.id WHERE f.fid=?",
                   [fid])
    row = cursor.fetchone()

    # Если пользователь не авторизован или это чужой файл
    if not row or (CURRENT_USER and row[0] != CURRENT_USER):
        log_syscall("sys_delete_file", {"fid": fid}, "failure")
        return False

    # Удаление файла
    cursor.execute("DELETE FROM files WHERE fid=?", [fid])
    conn.commit()

    log_syscall("sys_delete_file", {"fid": fid})
    return True

def sys_list_files(path="."):
    conn = get_connection()
    cursor = conn.cursor()

    # Простая выборка без фильтрации по каталогу (пока)
    cursor.execute("SELECT * FROM files ORDER BY created_at DESC LIMIT 10")
    rows = cursor.fetchall()

    result = []
    for r in rows:
        result.append({
            "fid": r["fid"],
            "path": r["path"],
            "owner_id": r["owner_id"]
        })

    log_syscall("sys_list_files", {"path": path})
    return result

def sys_exec(name: str):
    # Заглушка создания процесса
    conn = get_connection()
    cursor = conn.cursor()

    # Выделение фиктивной страницы памяти
    pages = ",".join(map(str, range(10)))  # Выделили 10 страниц

    # Создание записи о процессе
    cursor.execute("INSERT INTO processes (name, state, owner_id, memory_pages) "
                   "SELECT ?, 'created', u.id, ? FROM users AS u WHERE u.login=?",
                   [name, pages, CURRENT_USER])
    process_id = cursor.lastrowid
    conn.commit()

    log_syscall("sys_exec", {"name": name})
    return process_id

def sys_ps():
    conn = get_connection()
    cursor = conn.cursor()

    # Выборка процессов с именами владельцев
    cursor.execute("SELECT p.pid, p.name, p.state, u.login AS owner "
                   "FROM processes AS p LEFT JOIN users AS u ON p.owner_id=u.id "
                   "ORDER BY p.created_at DESC")
    rows = cursor.fetchall()

    result = []
    for r in rows:
        result.append({
            "pid": r["pid"],
            "name": r["name"],
            "state": r["state"],
            "owner": r["owner"] or "(system)"
        })

    log_syscall("sys_ps")
    return result

def sys_kill(pid: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Изменение состояния на terminated
    cursor.execute("UPDATE processes SET state='terminated' WHERE pid=? AND owner_id=(SELECT id FROM users WHERE login=?)",
                   [pid, CURRENT_USER])
    affected_rows = cursor.rowcount
    conn.commit()

    status = "success" if affected_rows > 0 else "failure"
    log_syscall("sys_kill", {"pid": pid}, status)
    return bool(affected_rows)

def sys_mem_alloc(size: int):
    # Просто возвращаем список адресов как строку
    addresses = list(range(1, size + 1))
    log_syscall("sys_mem_alloc", {"size": size})
    return ",".join(map(str, addresses))  # Возвращаем адреса строкой

def sys_logs(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM syscalls_log ORDER BY timestamp DESC LIMIT ?", [limit])
    rows = cursor.fetchall()

    result = []
    for r in rows:
        result.append(dict(r))

    log_syscall("sys_logs", {"limit": limit})
    return result

def sys_shutdown():
    log_syscall("sys_shutdown")
    return None

if __name__ == "__main__":
    # Тестовый запуск всех функций
    print(sys_login("admin", "password"))
    print(sys_whoami())
    print(sys_create_file("test.txt", "Hello World!"))
    print(sys_list_files("/home"))
    print(sys_logs(5))