from dotenv import load_dotenv
load_dotenv()

import os	
from time import sleep
import decimal
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
from variables import *

api_key = os.getenv('API_KEY')
api_secret = os.getenv('SECRET_KEY')

client = Client(api_key, api_secret)

name = 'ACMUSDT'
price = {name: None, 'error':False}

def usdt_pairs_trade(msg):
  ''' define how to process incoming WebSocket messages '''
  if msg['e'] != 'error':
    price[name] = float(msg['c'])
  else:
    price['error'] = True

bsm = BinanceSocketManager(client)
conn_key = bsm.start_symbol_ticker_socket(name, usdt_pairs_trade)
bsm.start()

while not price[name]:
  # wait for WebSocket to start streaming data
  sleep(0.1)

while True:
  # error check to make sure WebSocket is working
  if price['error']:
    # stop and restart socket
    bsm.stop_socket(conn_key)
    bsm.start()
    price['error'] = False

  else:
    if price[name] <= set_price:
      try:
        orderB1 = client.order_limit_buy(
	                  symbol=name,
	                  quantity=amount_1,
	                  price=str(price_1))
        break
      except BinanceAPIException as e:
        # error handling goes here
        print(e)
      except BinanceOrderException as e:
        # error handling goes here
        print(e)
  sleep(0.1)

bsm.stop_socket(conn_key)
reactor.stop()

'''
if price == open_price:
  orderB2 = client.order_limit_buy(
	        symbol=name,
	        quantity=amount_2, 
	        price=str(price_2))
  orderS1 = client.order_limit_sell(
	        symbol=name,
	        quantity=buy1, 
	        price=str(fix1))
  
  if price > fix1:
    result = client.cancel_order(
          symbol=name,
          orderId='orderId')
    break
  if price < price_2:
    orderB3 = client.order_limit_buy(
	          symbol=name,
	          quantity=amount_3,
	          price=str(price_3))
    orderS2 = client.order_limit_sell(
	          symbol=name,
	          quantity=buy12,
	          price=str(fix2))

    if price > fix2:
      break
    if price < price_3:
      orderB4 = client.order_limit_buy(
	            symbol=name,
	            quantity=amount_4,
	            price=str(price_4))
      orderS3 = client.order_limit_sell(
	            symbol=name,
	            quantity=buy123,
	            price=str(fix3))

      if price > fix3:
        break
      if price < price_4:
        orderB5 = client.order_limit_buy(
	              symbol=name,
	              quantity=amount_5,
	              price=str(price_5))
        orderS4 = client.order_limit_sell(
	              symbol=name,
	              quantity=buy1234,
	              price=str(fix4))
        
        if price > fix3:
          break
        if price < price_4:
          orderS5 = client.order_limit_buy(
	                symbol=name,
	                quantity=amount_5,
                  price=str(price_5))
'''