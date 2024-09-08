import sys
import platform
import aiohttp
import asyncio
from datetime import date
import time


today_date = date.today()
today_date_str = today_date.replace(day=today_date.day).strftime('%d.%m.%Y')
MAX_HISTORY_DAYS = 10


async def parse_response(json_response, currencies: list):
    parsed_dict = {}
    exchange_rate_list = json_response['exchangeRate']
    parsed_currencies_list = [el for el in exchange_rate_list if el['currency'] in currencies]
    for el in parsed_currencies_list:
        parsed_dict.update({el['currency']: {'sale': el['saleRate'], 'purchase': el['purchaseRate']}})
    return parsed_dict


async def fet_dates(number_of_days):
    list_of_dates = []
    for day in range(number_of_days):
        list_of_dates.append(today_date.replace(day=today_date.day - (day + 1)).strftime('%d.%m.%Y'))
    return list_of_dates


async def main(number_of_days, currencies: list):
    list_of_currencies = []
    list_of_days = await fet_dates(number_of_days)
    async with aiohttp.ClientSession() as session:
        for day in list_of_days:
            link_pb_api = f'https://api.privatbank.ua/p24api/exchange_rates?date={day}'
            async with session.get(link_pb_api) as response:
                if response.status == 200:
                    try:
                        json_result = await response.json()
                    except aiohttp.ClientConnectorError as err:
                        print(f'Connection error: {link_pb_api}', str(err))

                    list_of_currencies.append({day: await parse_response(json_result, currencies)})
        return list_of_currencies


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

