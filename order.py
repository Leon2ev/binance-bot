import numpy as np
import pandas as pd
import math
from datetime import datetime
from pandas import DataFrame as df
from binance.client import Client
from binance.enums import *
from binance.websockets import BinanceSocketManager

# client = Client()
# prices = client.get_all_tickers()

custom_symbol = 'BNBUSDT'
open_price = 210.15
first_order = 100

koef_order = 1.2
koef_price = 5
koef_fix = 10

order_1 = first_order
order_2 = round(order_1 * koef_order, 0)
order_3 = round(order_2 * koef_order, 0)
order_4 = round(order_3 * koef_order, 0)
order_5 = round(order_4 * koef_order, 0)

order12 = order_1 + order_2
order123 = order_1 + order_2 + order_3
order1234 = order_1 + order_2 + order_3 + order_4
order12345 = order_1 + order_2 + order_3 + order_4 + order_5

price_1 = open_price
price_2 = round(price_1 - price_1 * koef_price / 100, 2)
price_3 = round(price_2 - price_2 * koef_price * 1.2 / 100, 2)
price_4 = round(price_3 - price_3 * koef_price * 1.5 / 100, 2)
price_5 = round(price_4 - price_4 * koef_price * 2 / 100, 2)


amount_1 = round(order_1 / price_1, 2)
amount_2 = round(order_2 / price_2, 2)
amount_3 = round(order_3 / price_3, 2)
amount_4 = round(order_4 / price_4, 2)
amount_5 = round(order_5 / price_5, 2)

amount12 = amount_1 + amount_2
amount123 = amount_1 + amount_2 + amount_3
amount1234 = amount_1 + amount_2 + amount_3 + amount_4
amount12345 = amount_1 + amount_2 + amount_3 + amount_4 + amount_5

fix_1 = round((order_1 + order_1 * koef_fix / 100) / amount_1, 2)
fix_2 = round((order12 + order12 * koef_fix / 100) / amount12, 2)
fix_3 = round((order123 + order123 * koef_fix / 100) / amount123, 2)
fix_4 = round((order1234 + order1234 * koef_fix / 100) / amount1234, 2)
fix_5 = round((order12345 + order12345 * koef_fix / 100) / amount12345, 2)

orders = [order_1, order_2, order_3, order_4, order_5]
prices = [price_1, price_2, price_3, price_4, price_5]
amounts = [amount_1, amount_2, amount_3, amount_4, amount_5]
fixes = [fix_1, fix_2, fix_3, fix_4, fix_5]

print('num', 'amount', 'price', 'order', 'fix', 'total')
print('1.', amount_1, price_1, order_1, fix_1, amount_1)
print('2.', amount_2, price_2, order_2, fix_2, amount12)
print('3.', amount_3, price_3, order_3, fix_3, amount123)
print('4.', amount_4, price_4, order_4, fix_4, amount1234)
print('5.', amount_5, price_5, order_5, fix_5, amount12345)

#print(orders)
#print(prices)
#print(amounts)
#print(fixes)

'''
def int_r(num):
  num = int(num + (o.5 if num < 0 else -0.5))
  return num

order = client.create_test_order(
	symbol = custom_symbol,
	side=Client.SIDE_BUY,
	type=Client.ORDER_TYPE_MARKET,
	quantity=100)

def rd(x, y = 0):
  # A classical matematical rounding by Voznica
  m = int('1' + '0' * y) # multiplier - how many positions to the right
  q = x * m # shift to the right by multiplier
  c = int(q) # new number
  i = int((q-c) * 10) # indicator number on the right
  if i >= 5:
    c += 1
  return c/m

# определение числа знаков после запятой
import math
math.pi
print(len(str(math.pi).split('.')[1]))

from decimal import Decimal
print Decimal(str(0.25)).as_tuple().exponent*(-1)
'''

''' super
# long code
import decimal
x = '56.0001000'
x = x.rstrip('0') # returns '56.0001
x = decimal.Decimal(x) # returns Decimal('0.0001')
x = x.as_tuple().exponent # returns -4
x = abs(x)

# short code
abs(decimal.Decimal(x.rstrip('0')).as_tuple().exponent)
'''