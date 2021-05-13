from typing import Any, TypedDict

from binance import AsyncClient
from binance.exceptions import BinanceAPIException

from order import Order

class Parameters(TypedDict):
    SYMBOL: str
    OPEN_PRICE: float
    FIRST_ORDER_QUOTE: int
    COEFFICIENT_QUOTE: float
    COEFFICIENT_BASE: float
    COEFFICIENT_FIX: float
    COEFFICIENT_SET: int
    STEPS: int

class OrderManager():
    def __init__(self, client: AsyncClient):
            self.client = client
            self.orders_list: list[Order] = list() # list of orders instances

    async def place_buy_limit(self, order: Order) -> None:
        step = order.step
        try:
            buy_order = await self.client.order_limit_buy(
                symbol=order.symbol,
                quantity=order.buy_limit_base_volumes()[step],
                price=str(order.buy_limit_price_levels()[step])
            )
            order.buy_limit_id = buy_order['orderId']
        except BinanceAPIException as e:
            print(e)
        else:
            print(f'Step({step}) BUY limit for {order.symbol}, Price: {order.buy_limit_price_levels()[step]}, Amount: {order.buy_limit_base_volumes()[step]}')

    async def place_sell_limit(self, order: Order) -> None:
        step = order.step
        try:
            sell_order = await self.client.order_limit_sell(
                symbol=order.symbol,
                quantity=order.sell_limit_accumulated_base_volumes()[step],
                price=str(order.sell_limit_price_levels()[step]))
            order.sell_limit_id = sell_order['orderId']
        except BinanceAPIException as e:
            print(e)
        else:
            print(f'Step({step}) SELL limit for {order.symbol}, Price: {order.sell_limit_price_levels()[step]}, Amount {order.sell_limit_accumulated_base_volumes()[step]}')

    
    async def cancel_order(self, symbol: str, orderId: int) -> None:
        try:
            order = await self.client.cancel_order(symbol=symbol, orderId=orderId)
        except BinanceAPIException as e:
            print(e)
        else:
            status = order['status']
            side = order['side']
            order_type = order['type']
            order_symbol = order['symbol']
            print(f'{status} {side} {order_type} for: {order_symbol}')

    async def order_manager(self, order: Order, msg: dict) -> None:
        '''
        The main logic behind order placing. Place sell limit order when buy limit is filled.
        Remove order object and cancel open buy limit order if sell limit is filled.
        '''
        buy: bool = msg['S'] == 'BUY'
        sell: bool = msg['S'] == 'SELL'
        filled: bool = msg['X'] == 'FILLED'
        symbol: str = msg['s']
        
        if buy and filled and order.step < order.steps:
            orderId = order.sell_limit_id
            if orderId:
                await self.cancel_order(symbol=symbol, orderId=orderId)
                await self.place_sell_limit(order)
            else:
                await self.place_sell_limit(order)

            order.step += 1
            print(f'Pair: {order.symbol} Step: {order.step}')
            await self.place_buy_limit(order)
        elif sell and filled:
            orderId = order.buy_limit_id
            await self.cancel_order(symbol=symbol, orderId=orderId)
            print(f'Fix for: {order.symbol}')
            self.orders_list.remove(order)

    def handle_parameters(self, parameters: Parameters) -> None:

        '''Create instance of orders grid with received parameters and add it to the
        orders_list if instance for the same symbol is not already inside the list.'''

        is_in_list = list(filter(lambda x: x.symbol == parameters['SYMBOL'], self.orders_list))
        if not is_in_list:
            print('New pair added to the list:', parameters['SYMBOL'])
            self.orders_list.append(Order(parameters))

    async def tickers_stream_handler(self, tickers: Any) -> None:
        '''
        By default should receive list[dict].
        If get dict it's an error that will be hadled.
        '''
        if tickers == dict() and tickers['e'] == 'error':
            print(tickers['e'])
        else:
            for ticker in tickers:
                orders_to_place: list = list(filter(lambda x:
                    ticker['s'] == x.symbol and
                    float(ticker['c']) <= x.triger_buy_limit() and
                    x.initiated == False, self.orders_list))
                if orders_to_place:
                    for order in orders_to_place:
                        print(f'Pair: {order.symbol} Step: {order.step}')
                        await self.place_buy_limit(order)
                        order.initiated = True

    async def user_data_handler(self, msg: dict) -> None:
        '''
        Handle user account event stream.
        Check if executed order symbol is insde signal_list.
        Pass order object to order manager.
        '''
        error: bool = msg['e'] == 'error'
        execution: bool = msg['e'] == 'executionReport'
        if error:
            print(msg['e'])
        else:
            if self.orders_list and execution:
                order: Order = next(filter(lambda x: msg['s'] == x.symbol, self.orders_list))
                if order:
                    await self.order_manager(order, msg)
            else:
                print('Unhandled event:', msg['e'])
