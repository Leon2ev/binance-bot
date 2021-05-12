import asyncio
import os
from typing import Any

from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException, BinanceOrderException

from .orders import Orders
from .signals import Signals

api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")

# RTW channel
token: str = str(os.getenv("RTW_TOKEN"))
signals = Signals(token)
signal_list = signals.signal_list

async def main():
    # initialise the client
    client = await AsyncClient.create(api_key, secret_key, tld='us')

    # initialise websocket factory manager
    bsm = BinanceSocketManager(client)

    async def place_buy_limit(order: Orders) -> None:
        step = order.step
        try:
            buy_order = await client.order_limit_buy(
                symbol=order.symbol,
                quantity=order.buy_limit_base_volumes()[step],
                price=str(order.buy_limit_price_levels()[step]))
            order.buy_limit_id = buy_order['orderId']
        except BinanceAPIException as e:
            print(e)
        else:
            print(f'Step({step}) BUY limit for {order.symbol}, Price: {order.buy_limit_price_levels()[step]}, Amount: {order.buy_limit_base_volumes()[step]}')

    async def place_sell_limit(order: Orders) -> None:
        step = order.step
        try:
            sell_order = await client.order_limit_sell(
                symbol=order.symbol,
                quantity=order.sell_limit_accumulated_base_volumes()[step],
                price=str(order.sell_limit_price_levels()[step]))
            order.sell_limit_id = sell_order['orderId']
        except BinanceAPIException as e:
            print(e)
        else:
            print(f'Step({step}) SELL limit for {order.symbol}, Price: {order.sell_limit_price_levels()[step]}, Amount {order.sell_limit_accumulated_base_volumes()[step]}')

    async def cancel_order(symbol: str, orderId: int) -> None:
        try:
            order = await client.cancel_order(symbol=symbol, orderId=orderId)
        except BinanceAPIException as e:
            print(e)
        else:
            status = order['status']
            side = order['side']
            order_type = order['type']
            order_symbol = order['symbol']
            print(f'{status} {side} {order_type} for: {order_symbol}')

    async def order_manager(order: Orders, msg: dict) -> None:
        '''
        The main logic behind order placing. Place sell limit order when buy limit is filled.
        Remove order object and cancel open buy limit order if sell limit is filled.
        '''
        buy: bool = msg['S'] == 'BUY'
        sell: bool = msg['S'] == 'SELL'
        new: bool = msg['X'] == 'NEW'
        filled: bool = msg['X'] == 'FILLED'
        symbol: str = msg['s']
        
        if buy and filled and order.step < order.steps:
            orderId = order.sell_limit_id
            if orderId:
                await cancel_order(symbol=symbol, orderId=orderId)
                await place_sell_limit(order)
            else:
                await place_sell_limit(order)

            order.step += 1
            print(f'Pair: {order.symbol} Step: {order.step}')
            await place_buy_limit(order)
        elif sell and filled:
            orderId = order.buy_limit_id
            await cancel_order(symbol=symbol, orderId=orderId)
            print(f'Fix for: {order.symbol}')
            signal_list.remove(order)

    async def tickers_stream_handler(tickers: Any) -> None:
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
                    ticker['c'] <= x.triger_buy_limit() and
                    x.initiated == False, signal_list))
                if orders_to_place:
                    for order in orders_to_place:
                        print(f'Pair: {order.symbol} Step: {order.step}')
                        await place_buy_limit(order)
                        order.initiated = True

    async def user_data_handler(msg: dict) -> None:
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
            if signal_list and execution:
                order: Orders = next(filter(lambda x: msg['s'] == x.symbol, signal_list))
                if order:
                    await order_manager(order, msg)
            else:
                print('Unhandled event:', msg['e'])

    # create ticker socket listener
    async with bsm.miniticker_socket() as mts:
        while True:
            res = await mts.recv()
            await tickers_stream_handler(res)

    # create user socket listener
    async with bsm.user_socket() as us:
        while True:
            res = await us.recv()
            user_data_handler(res)

    await client.close_connection()


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.create_task(signals.run())
    loop.run_forever()
