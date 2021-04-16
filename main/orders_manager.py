import os
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

api_key = os.getenv("API_PUBLIC_BINANCE")
secret_key = os.getenv("API_SECRET_BINANCE")
client = Client(api_key, secret_key)
bsm = BinanceSocketManager(client)

# Get list of symbols from signals
symbols = list(map(lambda x: x['symbol'], signals))

# Handle tickers stream
def process_tickers(msg: list[dict]) -> None:
  if len(msg) > 0:
    # Get tickers only if signal presented
    filtered_tickers: list = list(filter(lambda x: x['s'] in symbols, msg))
    # Change ticker object and return only symbol and price
    tickers: list = list(map(lambda x: dict(symbol=x['s'], price=float(x['c'])), filtered_tickers))
    # Loop trough tickers and return list of matched ready to place orders.
    for ticker in tickers:
      # Compare ticker with signals. If ticker price <= signal set price add signal to the list
      orders_to_place: list = list(filter(lambda x: ticker['symbol'] == x['symbol'] and ticker['price'] <= x['set_price'], signals))
      # check if orders to place is not an emty list
      if len(orders_to_place) > 0:
        # loop trough list of orders and place limit
        for order in orders_to_place:
          print('Place buy order:', order)
      else:
        # print that list if order is empty
        print('No orders to place for:', ticker['symbol'])
  else:
    bsm.stop_socket(ticker_socket)
    reactor.stop()
    bsm.start()

# Handle user stream
def process_user_data(msg: dict) -> None:
  # эвент
  execution: bool = msg['e'] == 'executionReport'
  # то что будет использовать нижу
  buy: bool = msg['S'] == 'BUY'
  sell: bool = msg['S'] == 'SELL'
  order: dict = dict(symbol = msg['s'], price = msg['p'])
  if execution & buy:
    # если лимитник на покупку
    # сообщение будет приходить на любой выставленный ии сработанный
    # надо сделать что ловить только полностью заполненный ордер
    print('Buy: ', order)
  elif execution & sell:
    # тоже самое но на продажу
    print('Sell: ', order)
  else:
    # это просто для будущего/ можнно удалить
    print('Unhandled event: ', msg['e'])

ticker_socket = bsm.start_ticker_socket(process_tickers)
user_socket = bsm.start_user_socket(process_user_data)
bsm.start()