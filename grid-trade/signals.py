import json
from typing import TypedDict

import websockets

from orders import Orders

class Signal(TypedDict):
    SYMBOL: str
    OPEN_PRICE: float
    FIRST_ORDER_QUOTE: int
    COEFFICIENT_QUOTE: float
    COEFFICIENT_BASE: float
    COEFFICIENT_FIX: float
    COEFFICIENT_SET: int
    STEPS: int

class Signals():
    def __init__(self, token: str):
        self.token = token
        self.signal_list: list = list()

    def signal_symbols(self) -> list[str]:
        return list(map(lambda x: x.symbol, self.signal_list))

    def add_to_queue(self, signal: Signal) -> None:
        '''
        Create OrdersForPair instance with received signal parameters if it's not
        inside the queue list. Queue list can contain only one instance for symbol.
        '''
        in_queue = list(filter(lambda x: x.symbol == signal['SYMBOL'], self.signal_list))
        if not in_queue:
            print('New pair added to the queue:', signal['SYMBOL'])
            self.signal_list.append(Orders(signal))

    async def run(self) -> None:
        '''
        Websocket connection for RTW service.
        Receiving parameters for OrdersForPair object.
        '''
        uri = "wss://websocket.cioty.com/crypto/bot/1/channel"
        async with websockets.connect(uri) as websocket:
            await websocket.send('{"token":"' + self.token + '"}')
            print('Connected to rtw channel')
            while True:
                response = await websocket.recv()
                response_json = json.loads(response)
                signal: Signal = response_json['RTW']
                self.add_to_queue(signal)
