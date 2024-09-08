import sys
import platform
import aiohttp
import asyncio
from datetime import date
import time


LINK_TEMPLATE = 'https://api.privatbank.ua/p24api/exchange_rates?date={}'
MAX_HISTORY_DAYS = 10


async def parse_response(json_response, currencies: list):
    parsed_dict = {}
    exchange_rate_list = json_response['exchangeRate']
    parsed_currencies_list = [el for el in exchange_rate_list if el['currency'] in currencies]
    for el in parsed_currencies_list:
        parsed_dict.update({el['currency']: {'sale': el['saleRate'], 'purchase': el['purchaseRate']}})
    return parsed_dict


async def get_response(session, url, currencies: list):
    start_time = time.time()
    async with session.get(url) as response:
        if response.status == 200:
            json_result = await response.json()
            print(f'request for {url} took: {time.time() - start_time} seconds')
            return await parse_response(json_result, currencies)


async def make_links(number_of_days):
    list_of_links = []
    for i in range(number_of_days):
        day = date.today().replace(day=date.today().day - i).strftime('%d.%m.%Y')
        list_of_links.append(LINK_TEMPLATE.format(day))
    return list_of_links


async def main(number_of_days, currencies: list):
    list_of_links = await make_links(number_of_days)
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in list_of_links:
            tasks.append(get_response(session, url, currencies))
        return await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()
    currencies_list = ['USD', 'EUR']
    history_days = 1

    if len(sys.argv) == 2 and sys.argv[1].isdigit() and int(sys.argv[1]) <= MAX_HISTORY_DAYS:
        history_days = int(sys.argv[1])
    elif len(sys.argv) >= 3:
        _, history_days, *currencies_args = sys.argv
        currencies_list.extend(currencies_args)

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    request_result = asyncio.run(main(int(history_days), currencies_list))
    print(request_result)
    print(time.time() - start)

