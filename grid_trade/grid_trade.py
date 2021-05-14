import asyncio
import json
import os

import websockets
from binance import AsyncClient, BinanceSocketManager

from manager import OrderManager

api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")
token: str = str(os.getenv("RTW_TOKEN"))

async def main() -> None:

    client = await AsyncClient.create(api_key, secret_key, tld='com')

    bsm = BinanceSocketManager(client)

    manager = OrderManager(client)

    async def parameters_socket() -> None:

        '''Create RTW channel connection that will listen for incomming
        parameters which will be used to create Order class instance'''

        uri = "wss://websocket.cioty.com/crypto/bot/1/channel"
        async with websockets.connect(uri) as websocket:
            await websocket.send('{"token":"' + token + '"}')
            print('Connected to rtw channel')
            while True:
                res = await websocket.recv()
                res_json = json.loads(res)
                parameters = res_json['RTW']
                manager.handle_parameters(parameters)
                await asyncio.sleep(1)

    async def miniticker_socket(bsm) -> None:

        '''Binance websocket connection. Present list of mini tickers
        for all markets that have changed and pass it to the handler'''

        async with bsm.miniticker_socket() as mts:
            print('Connected to miniticker socket')
            while True:
                res = await mts.recv()
                await manager.handle_minitickers(res)
                await asyncio.sleep(1)

    async def user_socket(bsm) -> None:

        '''Binance websocket connection. Listen for all events from
        the users account and pass it to the handler'''

        async with bsm.user_socket() as us:
            print('Connected to user socket')
            while True:
                res = await us.recv()
                await manager.handle_user_data(res)
                await asyncio.sleep(1)

    await asyncio.gather(miniticker_socket(bsm), user_socket(bsm), parameters_socket())

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
