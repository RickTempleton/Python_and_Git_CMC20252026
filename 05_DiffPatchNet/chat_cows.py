#!/usr/bin/env python3

HOST = "0.0.0.0"
PORT = 1337

import asyncio
import shlex
import cowsay
import cmd

clients = {}   
COWS = set(cowsay.list_cows())


def free_cows():
    return sorted(COWS - set(clients))


class CowShell(cmd.Cmd):
    prompt = ""

    def __init__(self, writer):
        super().__init__()
        self.name = None
        self.writer = writer

    async def send(self, text=""):
        self.writer.write((text + "\n").encode())
        await self.writer.drain()

    def do_who(self, arg):
        """who — список зарегистрированных пользователей"""
        if arg.strip():
            asyncio.create_task(self.send("usage: who"))
            return
        asyncio.create_task(self.send(" ".join(sorted(clients)) or "nobody"))

    def do_cows(self, arg):
        """cows — свободные коровы"""
        if arg.strip():
            asyncio.create_task(self.send("usage: cows"))
            return
        asyncio.create_task(self.send(" ".join(free_cows()) or "no free cows"))

    def do_login(self, arg):
        """login NAME — зарегистрироваться"""
        try:
            args = shlex.split(arg)
        except ValueError:
            asyncio.create_task(self.send("parse error"))
            return

        if len(args) != 1:
            asyncio.create_task(self.send("usage: login NAME"))
            return

        if self.name is not None:
            asyncio.create_task(self.send("already logged in"))
            return

        new = args[0]

        if new not in COWS:
            asyncio.create_task(self.send("no such cow"))
            return

        if new in clients:
            asyncio.create_task(self.send("name is busy"))
            return

        clients[new] = asyncio.Queue()
        self.name = new

        asyncio.create_task(self.send(f"logged in as {new}"))

    def do_say(self, arg):
        """say NAME TEXT — личное сообщение"""
        if self.name is None:
            asyncio.create_task(self.send("login first"))
            return

        try:
            args = shlex.split(arg)
        except ValueError:
            asyncio.create_task(self.send("parse error"))
            return

        if len(args) < 2:
            asyncio.create_task(self.send("usage: say NAME TEXT"))
            return

        target = args[0]
        text = " ".join(args[1:])

        if target not in clients:
            asyncio.create_task(self.send("target not online"))
            return

        msg = cowsay.cowsay(text, cow=self.name)
        asyncio.create_task(clients[target].put(msg))
        asyncio.create_task(self.send(f"sent to {target}"))

    def do_yield(self, arg):
        """yield TEXT — сообщение всем"""
        if self.name is None:
            asyncio.create_task(self.send("login first"))
            return

        try:
            args = shlex.split(arg)
        except ValueError:
            asyncio.create_task(self.send("parse error"))
            return

        if not args:
            asyncio.create_task(self.send("usage: yield TEXT"))
            return

        text = " ".join(args)
        msg = cowsay.cowsay(text, cow=self.name)

        for name, q in clients.items():
            if name != self.name:
                asyncio.create_task(q.put(msg))

        asyncio.create_task(self.send("sent to everyone"))

    def do_quit(self, arg):
        """quit — выход"""
        if arg.strip():
            asyncio.create_task(self.send("usage: quit"))
            return
        return True

    def do_help(self, arg):
        """help — список команд"""
        if arg.strip():
            asyncio.create_task(self.send("usage: help"))
            return

        cmds = [
            "who",
            "cows",
            "login NAME",
            "say NAME TEXT",
            "yield TEXT",
            "quit",
            "help",
        ]
        asyncio.create_task(self.send("\n".join(cmds)))

    def default(self, line):
        asyncio.create_task(self.send("unknown command"))


async def chat(reader, writer):
    shell = CowShell(writer)

    await shell.send("type help")

    read_task = asyncio.create_task(reader.readline())
    recv_task = None

    try:
        while not reader.at_eof():
            tasks = [read_task]

            if shell.name is not None:
                if recv_task is None:
                    recv_task = asyncio.create_task(clients[shell.name].get())
                tasks.append(recv_task)

            done, _ = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                if task is read_task:
                    data = task.result()
                    if not data:
                        return

                    line = data.decode().strip()
                    read_task = asyncio.create_task(reader.readline())

                    result = shell.onecmd(line)

                    if result:
                        return

                elif recv_task is not None and task is recv_task:
                    msg = task.result()
                    writer.write(("\n" + msg + "\n").encode())
                    await writer.drain()
                    recv_task = asyncio.create_task(clients[shell.name].get())

    finally:
        read_task.cancel()
        if recv_task is not None:
            recv_task.cancel()

        if shell.name is not None and shell.name in clients:
            del clients[shell.name]

        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(chat, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())