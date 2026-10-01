from src import syscalls

def print_help():
    print("Доступные команды:")
    print("  help                 - показать справку")
    print("  whoami               - показать текущего пользователя")
    print("  login                - войти в систему")
    print("  create <path>        - создать файл")
    print("  read <path>          - прочитать файл")
    print("  ls                   - список файлов")
    print("  ps                   - список процессов")
    print("  logs <limit>         - показать логи")
    print("  exit                 - выход")

def main():
    current_user = 'guest'
    print("=== Welcome to StudyOS Kernel v0.1 ===")
    print("Type 'help' for commands list.")
    
    while True:
        try:
            command_line = input(f"{current_user}@studyos> ").strip()
            if not command_line:
                continue
            
            parts = command_line.split()
            cmd = parts[0]
            args = parts[1:]

            if cmd == 'help':
                print_help()
            elif cmd == 'whoami':
                print(f"Current user: {syscalls.sys_whoami(current_user)}")
            elif cmd == 'login':
                login = input("Login: ")
                password = input("Password: ")
                if syscalls.sys_login(login, password):
                    current_user = login
                    print(f"Welcome, {current_user}!")
                else:
                    print("Access denied.")
            elif cmd == 'create':
                if len(args) < 1:
                    print("Usage: create <path>")
                    continue
                path = args[0]
                content = input("Enter file content: ")
                fid = syscalls.sys_create_file(path, content, current_user)
                if fid != -1:
                    print(f"File '{path}' created with ID {fid}.")
                else:
                    print("Error creating file.")
            elif cmd == 'read':
                if len(args) < 1:
                    print("Usage: read <path>")
                    continue
                content = syscalls.sys_read_file(args[0], current_user)
                if content:
                    print(f"--- Content of {args[0]} ---")
                    print(content)
                else:
                    print("File not found or empty.")
            elif cmd == 'ls':
                files = syscalls.sys_list_files('/', current_user)
                print("Files in root:")
                for f in files:
                    print(f"  - {f}")
            elif cmd == 'ps':
                processes = syscalls.sys_ps(current_user)
                print("PID | Name | State")
                for p in processes:
                    print(f"{p['pid']} | {p['name']} | {p['state']}")
            elif cmd == 'logs':
                limit = int(args[0]) if args else 10
                logs = syscalls.sys_logs(limit, current_user)
                for log in logs:
                    print(f"[{log['timestamp']}] {log['name']} - {log['status']}")
            elif cmd == 'exit':
                syscalls.sys_shutdown(current_user)
                print("Shutting down. Bye.")
                break
            else:
                print(f"Unknown command: {cmd}")
        except Exception as e:
            print(f"System error: {e}")

if __name__ == "__main__":
    main()