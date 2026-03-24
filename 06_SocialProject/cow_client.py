#!/usr/bin/env python3

import ast
import cmd
import readline
import shlex
import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 1337


class Connection:
    """Соединение с сервером."""

    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port))
        self.rfile = self.sock.makefile("r", encoding="utf-8", newline="\n")
        self.wfile = self.sock.makefile("w", encoding="utf-8", newline="\n")

        self.alive = True

        self.req_id = 1
        self.waiting_id = None
        self.answer = None

        self.lock = threading.Lock()
        self.event = threading.Event()

    def request(self, command, args):
        """Отправить запрос серверу и дождаться ответа."""
        with self.lock:
            if not self.alive:
                return ""

            self.waiting_id = self.req_id
            self.req_id += 1

            self.answer = None
            self.event.clear()

            self.wfile.write(repr((self.waiting_id, command, args)) + "\n")
            self.wfile.flush()

            self.event.wait()
            return self.answer or ""

    def close(self):
        """Закрыть соединение и разблокировать ожидающий request()."""
        self.alive = False
        self.answer = ""
        self.event.set()

        try:
            self.rfile.close()
        except OSError:
            pass
        try:
            self.wfile.close()
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class Receiver(threading.Thread):
    """
    Фоновый поток чтения.

    (0, text)       -> обычное входящее сообщение
    (req_id, text)  -> ответ на текущий запрос
    """

    def __init__(self, conn, shell):
        super().__init__(daemon=True)
        self.conn = conn
        self.shell = shell

    def run(self):
        while self.conn.alive:
            try:
                line = self.conn.rfile.readline()
            except OSError:
                break

            if not line:
                self.conn.alive = False
                self.conn.answer = ""
                self.conn.event.set()
                sys.stdout.write("\n[server closed connection]\n")
                sys.stdout.write(self.shell.prompt + readline.get_line_buffer())
                sys.stdout.flush()
                break

            try:
                req_id, text = ast.literal_eval(line.strip())
            except Exception:
                continue

            if req_id == 0:
                sys.stdout.write("\r\033[K")
                sys.stdout.write("\n" + text + "\n")
                sys.stdout.write(self.shell.prompt + readline.get_line_buffer())
                sys.stdout.flush()
            elif req_id == self.conn.waiting_id:
                self.conn.answer = text
                self.conn.event.set()


class CowClient(cmd.Cmd):
    """Клиентская командная оболочка."""
    prompt = "> "

    def __init__(self, conn):
        super().__init__()
        self.conn = conn

    def emptyline(self):
        """Пустая строка ничего не делает."""
        pass

    def ask(self, command, args):
        """Отправить команду и вывести ответ сервера."""
        answer = self.conn.request(command, args)
        if answer:
            print(answer)
        return answer

    def do_who(self, arg):
        """Показать список подключённых пользователей."""
        if arg.strip():
            print("usage: who")
            return
        self.ask("who", [])

    def do_cows(self, arg):
        """Показать список свободных имён коров."""
        if arg.strip():
            print("usage: cows")
            return
        self.ask("cows", [])

    def do_login(self, arg):
        """Войти под именем коровы: login NAME"""
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("parse error")
            return

        if len(parts) != 1:
            print("usage: login NAME")
            return

        self.ask("login", [parts[0]])

    def do_say(self, arg):
        """Отправить личное сообщение: say NAME TEXT"""
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("parse error")
            return

        if len(parts) < 2:
            print("usage: say NAME TEXT")
            return

        target = parts[0]
        text = " ".join(parts[1:])
        self.ask("say", [target, text])

    def do_yield(self, arg):
        """Отправить сообщение всем: yield TEXT"""
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("parse error")
            return

        if not parts:
            print("usage: yield TEXT")
            return

        text = " ".join(parts)
        self.ask("yield", [text])

    def do_quit(self, arg):
        """Выйти из программы."""
        if arg.strip():
            print("usage: quit")
            return False

        self.ask("quit", [])
        self.conn.close()
        return True

    def do_EOF(self, arg):
        """Завершить работу по Ctrl+D."""
        print()
        return self.do_quit("")

    def complete_login(self, text, line, begidx, endidx):
        """Автодополнение login через cows."""
        response = self.conn.request("cows", [])
        if response in ("", "no free cows"):
            return []

        return [name for name in response.split() if name.startswith(text)]

    def complete_say(self, text, line, begidx, endidx):
        """Автодополнение первого аргумента say через who."""
        try:
            parts = shlex.split(line[:begidx])
        except ValueError:
            return []

        if len(parts) == 1:
            response = self.conn.request("who", [])
            if response in ("", "nobody"):
                return []
            return [name for name in response.split() if name.startswith(text)]

        return []


def main():
    host = HOST
    port = PORT

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    conn = Connection(host, port)
    shell = CowClient(conn)

    Receiver(conn, shell).start()

    try:
        while conn.alive:
            try:
                shell.cmdloop()
                break
            except KeyboardInterrupt:
                print("^C")
                print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()