import asyncio
import os

from binance import AsyncClient, BinanceSocketManager

from manager import OrderManager
from signals import Signals

api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")

token: str = str(os.getenv("RTW_TOKEN"))
signals = Signals(token)
signal_list = signals.signal_list

async def main() -> None:

    client = await AsyncClient.create(api_key, secret_key, tld='com')

    bsm = BinanceSocketManager(client)

    manager = OrderManager(client, signal_list)              

    async def miniticker_socket(bsm) -> None:
        # create ticker socket listener
        async with bsm.miniticker_socket() as mts:
            while True:
                res = await mts.recv()
                await manager.tickers_stream_handler(res)
                await asyncio.sleep(1)

    async def user_socket(bsm) -> None:
        # create user socket listener
        async with bsm.user_socket() as us:
            while True:
                res = await us.recv()
                await manager.user_data_handler(res)
                await asyncio.sleep(1)

    await asyncio.gather(miniticker_socket(bsm), user_socket(bsm))

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.create_task(signals.run())
    loop.run_until_complete(main())
