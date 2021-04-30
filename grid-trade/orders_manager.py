import os
from typing import Any
import asyncio
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from dotenv import load_dotenv

# Local classes
from signals import Signals
from orders import Orders

load_dotenv()  # take environment variables from .env.

''' Binance Client '''
api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")
client = Client(api_key, secret_key)
bsm = BinanceSocketManager(client)

''' RTW channel '''
token: str = str(os.getenv("RTW_TOKEN"))
signals = Signals(token)
signal_list = signals.signal_list
signal_symbols = signals.signal_symbols()

def filter_and_map_tickers(symbols: list[str], msg: list[dict]) -> list[dict]:
  '''
  Filter list of ticker objects with selected symbols.
  Map ticker object and return custom objects with needed properties.
  '''
  filtered: list[dict] = list(filter(lambda x: x['s'] in symbols, msg))
  tickers: list[dict] = list(map(lambda x: dict(symbol=x['s'], price=float(x['c'])), filtered))
  return tickers

def place_buy_limit(order: Orders) -> None:
  step = order.step
  buy_order = client.order_limit_buy(
    symbol=order.symbol,
    quantity=order.buy_limit_base_volumes()[step],
    price=str(order.buy_limit_price_levels()[step]))
  order.buy_limit_id = buy_order['orderId']
  print(f'Step({step}) BUY limit for {order.symbol}, Price: {order.buy_limit_price_levels()[step]}, Amount: {order.buy_limit_base_volumes()[step]}')

def place_sell_limit(order: Orders) -> None:
  step = order.step
  sell_order = client.order_limit_sell(
    symbol=order.symbol,
    quantity=order.sell_limit_accumulated_base_volumes()[step],
    price="{:.2f}".format(order.sell_limit_price_levels()[step]))
  order.sell_limit_id = sell_order['orderId']
  print(f'Step({step}) SELL limit for {order.symbol}, Price: {order.sell_limit_price_levels()[step]}, Amount {order.sell_limit_accumulated_base_volumes()[step]}')

def place_first_orders(tickers: list[dict]) -> None:
  '''
  Here we place the first buy limit order if all conditions below will be fulfilled.
  '''
  for ticker in tickers:
    orders_to_place: list = list(filter(lambda x:
    ticker['symbol'] == x.symbol and
    ticker['price'] <= x.triger_buy_limit() and
    x.initiated == False, signal_list))
    if orders_to_place:
      for order in orders_to_place:
        print(f'Pair: {order.symbol} Step: {order.step}')
        place_buy_limit(order)
        order.initiated = True

def order_manager(order: Orders, msg: dict) -> None:
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
      client.cancel_order(symbol=symbol, orderId=orderId)
      place_sell_limit(order)
    else:
      place_sell_limit(order)

    order.step += 1
    print(f'Pair: {order.symbol} Step: {order.step}')
    place_buy_limit(order)
  elif sell and filled:
    orderId = order.buy_limit_id
    client.cancel_order(symbol=symbol, orderId=orderId)
    print(f'Buy limit canceled for: {order.symbol}')
    print(f'Fix for: {order.symbol}')
    signal_list.remove(order)

def tickers_stream_handler(msg: Any) -> None:
  '''
  By default should receive list[dict].
  If get dict it's an error that will be hadled.
  '''
  if msg == dict() and msg['e'] == 'error':
    print(msg['e'])
    bsm.stop_socket(ticker_socket)
    bsm.start()
  else:
    tickers = filter_and_map_tickers(signal_symbols, msg)
    place_first_orders(tickers)

def user_data_handler(msg: dict) -> None:
  error: bool = msg['e'] == 'error'
  execution: bool = msg['e'] == 'executionReport'
  if error:
    print(msg['e'])
    bsm.stop_socket(user_socket)
    bsm.start()
  else:
    if signal_list and execution:
      order: Orders = next(filter(lambda x: msg['s'] == x.symbol, signal_list))
      if order:
        order_manager(order, msg)
    else:
      print('Unhandled event: ', msg['e'])

''' Binance socket instances '''
ticker_socket = bsm.start_miniticker_socket(tickers_stream_handler)
user_socket = bsm.start_user_socket(user_data_handler)
bsm.start()

''' RTW channel instances '''
asyncio.get_event_loop().run_until_complete(signals.run())