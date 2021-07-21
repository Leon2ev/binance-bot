from typing import Any, TypedDict, Union

from binance import AsyncClient
from binance.exceptions import BinanceAPIException

from order import Order
from backup import OrderListBackup


# Incomming parameters type that will be received from RTW
class Parameters(TypedDict):
    SYMBOL: str
    OPEN_PRICE: float
    FIRST_ORDER_QUOTE: int
    COEFFICIENT_QUOTE: float
    COEFFICIENT_BASE: float
    COEFFICIENT_FIX: float
    COEFFICIENT_SET: int
    STEPS: int
    DELETE: Union[bool, None]


class OrderManager(OrderListBackup):
    def __init__(self, client: AsyncClient):
            self.client = client
            self.orders_list: list[Order] = list() # list of Order instances

    
    def fetch_orders_list_backup(self) -> None:
        # Fetch orders_list from DB
        backup = self.get_orders_list_backup()

        if backup:
            for item in backup:
                order: Order = Order(item, backup=True)
                self.orders_list.append(order)
            
            symbols_list = [o.symbol for o in self.orders_list]
            print('Pairs in queue:', symbols_list)


    async def place_buy_limit(self, order: Order) -> None:
        step = order.step

        try:
            buy_order = await self.client.order_limit_buy(
                symbol=order.symbol,
                quantity=order.buy_quantity()[step],
                price=str(order.buy_level()[step])
            )
            order.buy_limit_id = buy_order['orderId']
        except BinanceAPIException as e:
            print(e)
        else:
            print(f'Step({step}) BUY limit for {order.symbol}, Price: {order.buy_level()[step]}, Amount: {order.buy_quantity()[step]}')


    async def place_sell_limit(self, order: Order) -> None:
        step = order.step

        try:
            sell_order = await self.client.order_limit_sell(
                symbol=order.symbol,
                quantity=order.sell_quantity()[step],
                price=str(order.sell_level()[step])
            )
            order.sell_limit_id = sell_order['orderId']
        except BinanceAPIException as e:
            print(e)
        else:
            print(f'Step({step}) SELL limit for {order.symbol}, Price: {order.sell_level()[step]}, Amount {order.sell_quantity()[step]}')

    
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

    
    async def add_filters(self, order: Order) -> Order:
        # https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#filters

        symbol_info  = await self.client.get_symbol_info(order.symbol)
        if symbol_info:
            symbol_filters = symbol_info['filters']
            price_filter = next(filter(lambda x: "PRICE_FILTER" == x['filterType'], symbol_filters))
            lot_size = next(filter(lambda x: "LOT_SIZE" == x['filterType'], symbol_filters))
            order.tick_size = float(price_filter['tickSize'])
            order.step_size = float(lot_size['stepSize'])

        return order


    def add_order(self, order: Order) -> None:
        # Add order to orders list and update backup
        self.orders_list.append(order)
        self.insert_item(order.__dict__)


    def remove_order(self, order: Order) -> None:
        # Remove order from orders list and update backup
        self.orders_list.remove(order)
        self.delete_item(order.symbol)


    async def manager(self, order: Order, msg: dict) -> None:
        
        '''The main logic behind order placing. Place sell limit order when buy limit is filled.
        Remove Order class instance and cancel open buy limit order if sell limit is filled'''

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
            await self.place_buy_limit(order)
            print(f'Pair: {order.symbol} Step: {order.step}')

        elif sell and filled:
            orderId = order.buy_limit_id
            await self.cancel_order(symbol=symbol, orderId=orderId)
            self.remove_order(order)
            print(f'Fix for: {order.symbol}')


    async def handle_parameters(self, parameters: Parameters) -> None:

        '''Create instance of Order class with received parameters and add it to the
        orders_list if instance with the same symbol is not already inside the list'''

        in_list = list(filter(lambda x: x.symbol == parameters['SYMBOL'], self.orders_list))

        if not in_list and not parameters['DELETE']:
            order = Order(parameters)
            order = await self.add_filters(order)
            self.add_order(order)
            symbols_list = [o.symbol for o in self.orders_list]

            print('Pair added:', parameters['SYMBOL'])
            print('Pairs in queue:', symbols_list)
        elif in_list and parameters['DELETE']:
            order = next(filter(lambda x: x.symbol == parameters['SYMBOL'], self.orders_list))
            self.remove_order(order)
            symbols_list = [o.symbol for o in self.orders_list]

            print('Pair removed:', parameters['SYMBOL'])
            print('Pairs in queue:', symbols_list)
        else:
            if parameters['DELETE']:
                print('Pair is not in queue:', parameters['SYMBOL'])
            else:
                print('Pair already in queue:', parameters['SYMBOL'])


    async def handle_minitickers(self, tickers: Any) -> None:
        
        '''By default should receive list[dict].
        If get dict it's an error that will be handled'''

        if tickers == dict() and tickers['e'] == 'error':
            print('Tickers error:', tickers['e'])
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


    async def handle_user_data(self, msg: dict) -> None:
        
        '''Handle user account event stream.
        If executed order symbol is inside the order_list
        pass this Order class instance to manager'''

        error: bool = msg['e'] == 'error'
        execution: bool = msg['e'] == 'executionReport'

        if error:
            print(msg['e'])
        else:
            if execution and any([x.symbol == msg['s'] for x in self.orders_list]):
                order: Order = next(filter(lambda x: msg['s'] == x.symbol, self.orders_list))
                if order:
                    await self.manager(order, msg)
            else:
                print('Unhandled event:', msg['e'])
