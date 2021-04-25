import os
import asyncio
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
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

def filter_and_map_tickers(symbols: list[str], data: list[dict]) -> list[dict]:
  '''
  Filter list of ticker objects with selected symbols.
  Map ticker object and return custom objects with needed properties.
  '''
  filtered: list[dict] = list(filter(lambda x: x['s'] in symbols, data))
  tickers: list[dict] = list(map(lambda x: dict(symbol=x['s'], price=float(x['c'])), filtered))
  return tickers

def place_buy_limit(order: Orders) -> None:
  step = order.step
  client.order_limit_buy(
    symbol=order.symbol,
    quantity=order.buy_limit_base_volumes()[step],
    price=str(order.buy_limit_price_levels()[step]))
  print(f'Step({step}) BUY limit for {order.symbol}, Price: {order.open_price}, Amount: {order.buy_limit_base_volumes()[step]}')

def place_sell_limit(order: Orders) -> None:
  step = order.step
  client.order_limit_sell(
    symbol=order.symbol,
    quantity=order.sell_limit_accumulated_base_volumes()[step],
    price=str(order.sell_limit_price_levels()[step]))
  print(f'Step({step}) SELL limit for {order.symbol}, Price: {order.sell_limit_price_levels()[step]}, Amount {order.sell_limit_accumulated_base_volumes()[step]}')

def place_first_orders(tickers: list[dict]) -> None:
  '''
  Here we place the first buy limit order if all conditions below will be fulfilled.
  Sell limit will be placed next after buy limit.
  '''
  for ticker in tickers:
    orders_to_place: list = list(filter(lambda x:
    ticker['symbol'] == x.symbol and
    ticker['price'] <= x.triger_buy_limit() and
    x.step < 1, signal_list))
    if orders_to_place:
      for order in orders_to_place:
        place_buy_limit(order)
        place_sell_limit(order)
        order.step = 1
        print(f'Pair: {order.symbol} Step: {order.step}')

def order_manager(order: Orders, msg: dict) -> None:
  '''
  This will work only when you have active buy and sell limit orders placed by place_first_orders.
  If a buy limit order is FILLED, a sell limit order will be canceled and both buy and sell new orders
  will be placed. It will continue until last steps limit is reached.
  '''
  buy: bool = msg['S'] == 'BUY'
  sell: bool = msg['S'] == 'SELL'
  symbol: str = msg['s']
  if buy and order.step < order.steps:
    open_orders = client.get_open_orders(symbol=symbol) # response should contain single sell limit order
    open_sell_limit_order_id = open_orders[0]['orderId'] # get id of open sell limit order
    client.cancel_order(symbol=symbol, orderId=open_sell_limit_order_id)
    place_buy_limit(order)
    place_sell_limit(order)
    order.step += 1
  elif sell:
    signal_list.remove(order)

def tickers_stream_handler(data: list[dict]) -> None:
  if data:
    symbols: list[str] = list(map(lambda x: x.symbol, signal_list))
    tickers = filter_and_map_tickers(symbols, data)
    place_first_orders(tickers)
  else:
    bsm.stop_socket(ticker_socket)
    reactor.stop()
    bsm.start()

def user_data_handler(msg: dict) -> None:
  execution: bool = msg['e'] == 'executionReport'
  order: Orders = next(filter(lambda x: msg['s'] == x.symbol, signal_list))
  if execution and order:
    filled: bool = msg['X'] == 'FILLED'
    if filled:
      order_manager(order, msg)
  else:
    print('Unhandled event: ', msg['e'])

''' Binance socket instances '''
ticker_socket = bsm.start_ticker_socket(tickers_stream_handler)
user_socket = bsm.start_user_socket(user_data_handler)
bsm.start()

''' RTW channel instances '''
asyncio.get_event_loop().run_until_complete(signals.run())