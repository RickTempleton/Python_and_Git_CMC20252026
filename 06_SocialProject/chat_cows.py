#!/usr/bin/env python3

import asyncio
import ast
import shlex
import cowsay

HOST = "0.0.0.0"
PORT = 1337

clients = {}

all_cows = set(cowsay.list_cows())


def free_cows():
    """Свободные имена коров."""
    return sorted(all_cows - set(clients))


async def send(writer, req_id, text):
    """
    Отправить клиенту кортеж:
    (req_id, text)
    """
    writer.write((repr((req_id, text)) + "\n").encode())
    await writer.drain()


async def process_command(user, writer, req_id, command, args):
    """
    Сервер получает уже готовые данные:
    command -- строка
    args    -- список аргументов

    Клиент уже проверил синтаксис команды,
    поэтому сервер занимается только логикой чата.
    """

    disconnect = False
    response = "unknown command"

    match command:
        case "who":
            response = " ".join(sorted(clients)) or "nobody"

        case "cows":
            response = " ".join(free_cows()) or "no free cows"

        case "login":
            name = args[0]

            if user["name"] is not None:
                response = "already logged in"
            elif name not in all_cows:
                response = "no such cow"
            elif name in clients:
                response = "name is busy"
            else:
                user["name"] = name
                clients[name] = user["queue"]
                response = f"logged in as {name}"

        case "say":
            if user["name"] is None:
                response = "login first"
            else:
                target = args[0]
                text = args[1]

                if target not in clients:
                    response = "target not online"
                else:
                    msg = cowsay.cowsay(text, cow=user["name"])
                    await clients[target].put(msg)
                    response = f"sent to {target}"

        case "yield":
            if user["name"] is None:
                response = "login first"
            else:
                text = args[0]
                msg = cowsay.cowsay(text, cow=user["name"])

                for name, q in clients.items():
                    if name != user["name"]:
                        await q.put(msg)

                response = "sent to everyone"

        case "quit":
            response = "bye"
            disconnect = True
        
        case _:
            response = "Error"


    await send(writer, req_id, response)
    return disconnect


async def chat(reader, writer):
    """Обработка одного клиента."""

    user = {
        "name": None,
        "queue": asyncio.Queue(),
    }

    await send(writer, 0, "Please login")

    try:
        while True:
            read_task = asyncio.create_task(reader.readline())
            msg_task = asyncio.create_task(user["queue"].get())

            done, pending = await asyncio.wait(
                [read_task, msg_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if read_task in done:
                data = read_task.result()

                if not data:
                    msg_task.cancel()
                    break

                msg_task.cancel()

                try:
                    req_id, command, args = ast.literal_eval(data.decode().strip())
                except Exception:
                    await send(writer, 0, "bad request format")
                    continue

                if await process_command(user, writer, req_id, command, args):
                    break

            if msg_task in done:
                text = msg_task.result()

                read_task.cancel()
                await send(writer, 0, text)

    finally:
        if user["name"] is not None:
            clients.pop(user["name"], None)

        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(chat, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())