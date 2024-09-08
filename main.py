import asyncio
import platform
import sys
from datetime import date, timedelta

import aiohttp

LINK_TEMPLATE = "https://api.privatbank.ua/p24api/exchange_rates?date={}"
MAX_HISTORY_DAYS = 10

currencies_list = ["EUR", "USD"]
history_days = 1


async def parse_response(json_response, currencies: list):
    parsed_dict = {}
    date_from_response = json_response["date"]
    exchange_rate_list = json_response["exchangeRate"]
    parsed_currencies_list = [
        el for el in exchange_rate_list if el["currency"] in currencies
    ]
    for el in parsed_currencies_list:
        parsed_dict.update(
            {el["currency"]: {"sale": el["saleRate"], "purchase": el["purchaseRate"]}}
        )
    return {date_from_response: parsed_dict}


async def get_response(session, url, currencies: list):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                json_result = await response.json()
                return await parse_response(json_result, currencies)
    except aiohttp.ClientConnectorError as err:
        print(f"Connection error: {url}", str(err))
    except aiohttp.ClientResponseError as err:
        print(f"Server response error: {url}", str(err))
    except asyncio.TimeoutError:
        print(f"Request timed out for {url}")


async def make_links(number_of_days):
    list_of_links = []
    for i in range(number_of_days):
        day = date.today() - timedelta(days=i)
        list_of_links.append(LINK_TEMPLATE.format(day.strftime("%d.%m.%Y")))
    return list_of_links


async def main(currencies: list, number_of_days=1):
    list_of_links = await make_links(number_of_days)
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in list_of_links:
            tasks.append(get_response(session, url, currencies))
        return await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    if (
        len(sys.argv) == 2
        and sys.argv[1].isdigit()
        and int(sys.argv[1]) <= MAX_HISTORY_DAYS
    ):
        history_days = int(sys.argv[1])
    elif (
        len(sys.argv) >= 3
        and sys.argv[1].isdigit()
        and int(sys.argv[1]) <= MAX_HISTORY_DAYS
    ):
        _, history_days, *currencies_args = sys.argv
        currencies_list.extend(currencies_args)

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    request_result = asyncio.run(main(currencies_list, int(history_days)))
    print(request_result)
