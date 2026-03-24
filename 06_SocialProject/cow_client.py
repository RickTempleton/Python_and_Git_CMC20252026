#!/usr/bin/env python3

import socket
import threading
import readline
import sys

HOST = "127.0.0.1"
PORT = 1337
PROMPT = "> "


class Client:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port))
        self.alive = True
        self.lock = threading.Lock()

    def send(self, line):
        with self.lock:
            self.sock.sendall((line + "\n").encode())

    def close(self):
        self.alive = False
        try:
            self.sock.close()
        except OSError:
            pass


def receiver(client):
    while client.alive:
        try:
            data = client.sock.recv(4096)
            if not data:
                print("\n[server closed connection]")
                break

            text = data.decode()

            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")

            sys.stdout.write(PROMPT + readline.get_line_buffer())
            sys.stdout.flush()

        except OSError:
            break


def main():
    host = HOST
    port = PORT

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    client = Client(host, port)
    t = threading.Thread(target=receiver, args=(client,), daemon=True)
    t.start()

    try:
        while client.alive:
            try:
                line = input(PROMPT)
            except EOFError:
                line = "quit"
                print()
            except KeyboardInterrupt:
                print()
                continue

            if not line.strip():
                continue

            readline.add_history(line)
            client.send(line)

            if line.strip() == "quit":
                break

    finally:
        client.close()


if __name__ == "__main__":
    main()