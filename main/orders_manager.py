import os
import asyncio
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
from dotenv import load_dotenv

from signals import Signals

load_dotenv()  # take environment variables from .env.

''' Binance Client '''
api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")
client = Client(api_key, secret_key)
bsm = BinanceSocketManager(client)

''' RTW channel '''
token = os.getenv("RTW_TOKEN")
signals = Signals(token)
signal_list = signals.signal_list

def filter_and_map_tickers(s: list[str], m: list[dict]) -> list[dict]:
  filtered: list[str] = list(filter(lambda x: x['s'] in s, m))
  tickers: list[dict] = list(map(lambda x: dict(symbol=x['s'], price=float(x['c'])), filtered))
  return tickers

def tickers_stream_handler(msg: list[dict]) -> None:
  if msg:
    symbols: list[str] = list(map(lambda x: x.symbol, signal_list))
    tickers = filter_and_map_tickers(symbols, msg)
    for ticker in tickers:
      orders_to_place: list = list(filter(lambda x: ticker['symbol'] == x.symbol and ticker['price'] <= x.triger_buy_limit(), signal_list))
      if orders_to_place:
        for order in orders_to_place:
          print('Place buy order:', order.symbol, order.open_price)
      else:
        print('No orders to place for:', ticker['symbol'])
  else:
    bsm.stop_socket(ticker_socket)
    reactor.stop()
    bsm.start()

def process_user_data(msg: dict) -> None:
  execution: bool = msg['e'] == 'executionReport'
  buy: bool = msg['S'] == 'BUY'
  sell: bool = msg['S'] == 'SELL'
  order: dict = dict(symbol = msg['s'], price = msg['p'])
  if execution & buy:
    print('Buy: ', order)
  elif execution & sell:
    print('Sell: ', order)
  else:
    print('Unhandled event: ', msg['e'])

''' Binance socket instances '''
ticker_socket = bsm.start_ticker_socket(tickers_stream_handler)
user_socket = bsm.start_user_socket(process_user_data)
bsm.start()

''' RTW channel instances '''
asyncio.get_event_loop().run_until_complete(signals.run())