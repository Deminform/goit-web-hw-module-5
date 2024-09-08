import asyncio
import logging
from datetime import datetime

import names
import websockets
from aiofile import async_open
from aiopath import AsyncPath
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

from main import main as currency_exchange_main

logging.basicConfig(level=logging.INFO)
log_path = AsyncPath("exchange_request_log.txt")


class Server:
    clients = set()
    BASE_CURRENCIES = ["EUR", "USD"]

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            for client in self.clients:
                await client.send(message)

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.split(" ", 1)[0] == "exchange":
                result = await self.parse_command(message)
                log_msg = message
                message = await currency_exchange_main(result[0], result[1])
                await self.make_log(ws.name, log_msg, message)
                message = await self.format_exchange_response(message)
            await self.send_to_clients(f"<br><b>{ws.name}</b>: {message}")

    async def parse_command(self, message: str):
        new_list = self.BASE_CURRENCIES.copy()
        if len(message.split(" ")) == 2 and message.split(" ")[1].isdigit():
            _, days = message.split(" ")
            return new_list, int(days)
        elif len(message.split(" ")) >= 3 and message.split(" ")[1].isdigit():
            _, days, *currency = message.split(" ")
            new_list.extend(currency)
            return new_list, int(days)
        else:
            return new_list, 1

    @staticmethod
    async def format_exchange_response(message) -> str:
        result = []
        for record in message:
            for date, currencies in record.items():
                result.append(f"<br>{date}")
                for currency, rates in currencies.items():
                    sale = rates["sale"]
                    purchase = rates["purchase"]
                    result.append(
                        f"{currency} : sale {"{:.2f}".format(sale)}, purchase {"{:.2f}".format(purchase)} |"
                    )
        return "<br>".join(result)

    @staticmethod
    async def make_log(name, message, response):
        async with async_open(log_path, "a") as afp:
            await afp.write(
                f'{name}: made a request at: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")} '
                f"/ request is: {message} "
                f"/ response is: {response}\n"
            )


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
