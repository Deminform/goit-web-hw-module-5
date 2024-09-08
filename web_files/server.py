import asyncio
import logging
import websockets
import names
from prettytable import PrettyTable

from main import main as currency_exchange_main
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()
    BASE_CURRENCIES = ['EUR', 'USD']

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

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
            if message.split(' ', 1)[0] == 'exchange':
                result = await self.parse_command(message)
                message = await currency_exchange_main(result[0], result[1])
                message = await self.format_exchange_response(message)
            await self.send_to_clients(f"{ws.name}: {message}")

    async def parse_command(self, message: str):
        if len(message.split(' ')) == 2:
            _, days = message.split(' ')
            return self.BASE_CURRENCIES, int(days)
        elif len(message.split(' ')) >= 3:
            _, days, *currency = message.split(' ')
            self.BASE_CURRENCIES.extend(currency)
            return self.BASE_CURRENCIES, int(days)
        else:
            return self.BASE_CURRENCIES, 1

    @staticmethod
    async def format_exchange_response(message) -> str:
        result = []
        for record in message:
            for date, currencies in record.items():
                result.append(f'<br>{date}')
                for currency, rates in currencies.items():
                    sale = rates['sale']
                    purchase = rates['purchase']
                    result.append(f"{currency} : sale {"{:.2f}".format(sale)}, purchase {"{:.2f}".format(purchase)} |")
        return "<br>".join(result)


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
