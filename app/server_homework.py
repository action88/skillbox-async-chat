# -*- coding: utf-8 -*-
import asyncio
from asyncio import transports
from typing import List, Any


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    history: List[str] = list()
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data.decode('utf-8', 'ignore').strip())

        decoded = data.decode('utf-8', 'ignore').strip()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login: ", "\r\n").replace("\r\n", "")
                if self.login in self.server.login:
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой\n".encode())
                    self.transport.close()
                else:
                    self.server.add_login(self.login)
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.save_history(message)
        for user in self.server.clients:
            user.transport.write(message.encode())

    def save_history(self, massage: str):
        self.history.append(massage)

    def send_history(self):
        self.transport.write(f"{self.history[-10:]}".encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.login = []

    def add_login(self, login: str):
        self.login.append(login)

    def remove_login(self, login: str):
        self.login.remove(login)

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
