import asyncio
import json
import os
import time

import websockets
from binance import AsyncClient, BinanceSocketManager

from manager import OrderManager

api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")
parameters_url = os.getenv("PARAMETERS_URL")
token: str = str(os.getenv("RTW_TOKEN"))

async def main() -> None:

    client = await AsyncClient.create(api_key, secret_key, tld='com')

    bsm = BinanceSocketManager(client)

    manager = OrderManager(client)
    manager.fetch_orders_list_backup()

    async def parameters_socket() -> None:

        '''Create RTW channel connection that will listen for incomming
        parameters which will be used to create Order class instance'''

        async with websockets.connect(parameters_url) as websocket:
            await websocket.send('{"token":"' + token + '"}')
            print('Connected to RTW channel')
            while True:
                if websocket.open:
                    res = await websocket.recv()
                    res_json = json.loads(res)
                    parameters = res_json['RTW']
                    await manager.handle_parameters(parameters)
                else:
                    break

            print('RTW channel connection lost')
            print('Trying to reconnect...')
            time.sleep(5)
            await parameters_socket()


    async def miniticker_socket(bsm) -> None:

        '''Binance websocket connection. Present list of mini tickers
        for all markets that have changed and pass it to the handler'''

        async with bsm.miniticker_socket() as mts:
            print('Connected to miniticker socket')
            while True:
                res = await mts.recv()
                await manager.handle_minitickers(res)


    async def user_socket(bsm) -> None:

        '''Binance websocket connection. Listen for all events from
        the users account and pass it to the handler'''

        async with bsm.user_socket() as us:
            print('Connected to user socket')
            while True:
                res = await us.recv()
                if res:
                    await manager.handle_user_data(res)


    user_socket_task = asyncio.create_task(user_socket(bsm))
    miniticker_socket_task = asyncio.create_task(miniticker_socket(bsm))
    parameters_socket_task = asyncio.create_task(parameters_socket())
    
    await user_socket_task
    await miniticker_socket_task
    await parameters_socket_task

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
