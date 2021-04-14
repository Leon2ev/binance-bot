import numpy as np
import pandas as pd
import decimal
from pandas import DataFrame as df

first_usdt = 20
open_price = 26.38
a = abs(decimal.Decimal(
          str(open_price).rstrip('0')).as_tuple().exponent)
set_price = round(open_price + open_price / 800, a)
koef_usdt = 1.2
koef_price = 1
koef_fix = 2
print('base: ' 'first usdt =', first_usdt, 'open price =', open_price, 'set price =', set_price, 'koef usdt =', koef_usdt, 'koef price =', koef_price, 'koef fix =', koef_fix)

# расчет стоимости buy-limit ордеров в usdt
usdt_1 = int(first_usdt)
usdt_2 = int(round(usdt_1 * koef_usdt, 0))
usdt_3 = int(round(usdt_2 * koef_usdt, 0))
usdt_4 = int(round(usdt_3 * koef_usdt, 0))
usdt_5 = int(round(usdt_4 * koef_usdt, 0))
print('orders in USDT:', usdt_1, usdt_2, usdt_3, usdt_4, usdt_5)

# расчетные ценовые уровни для buy-limit ордеров
price_1 = open_price
price_2 = round(price_1 - price_1 * koef_price / 100, a)
price_3 = round(price_2 - price_2 * koef_price * 1.2 / 100, a)
price_4 = round(price_3 - price_3 * koef_price * 1.5 / 100, a)
price_5 = round(price_4 - price_4 * koef_price * 2 / 100, a)
print('prices for buy-limit:', price_1, price_2, price_3, price_4, price_5)

# количество монет актива в ордерах
if a == 1: b = 3
if a == 2: b = 2
if a == 3: b = 1
if a == 4: b = 0
amount_1 = round(usdt_1 / price_1, b)
amount_2 = round(usdt_2 / price_2, b)
amount_3 = round(usdt_3 / price_3, b)
amount_4 = round(usdt_4 / price_4, b)
amount_5 = round(usdt_5 / price_5, b)
print('orders buy-limit:', amount_1, amount_2, amount_3, amount_4, amount_5)

# соответствующие суммы открытых buy-limit ордеров
usdt1 = usdt_1
usdt12 = usdt_1 + usdt_2
usdt123 = usdt_1 + usdt_2 + usdt_3
usdt1234 = usdt_1 + usdt_2 + usdt_3 + usdt_4
usdt12345 = usdt_1 + usdt_2 + usdt_3 + usdt_4 + usdt_5
print('summa in USDT:', usdt1, usdt12, usdt123, usdt1234, usdt12345)

# размер sell-limit ордеров в монетах
buy1 = amount_1
buy12 = amount_1 + amount_2
buy123 = amount_1 + amount_2 + amount_3
buy1234 = amount_1 + amount_2 + amount_3 + amount_4
buy12345 = amount_1 + amount_2 + amount_3 + amount_4 + amount_5
print('orders sell-limit:', buy1, buy12, buy123, buy1234, buy12345)

# расчетные ценовые уровни для sell-limit ордеров
fix1 = round((usdt1 + usdt1 * koef_fix / 100) / buy1, a)
fix2 = round((usdt12 + usdt12 * koef_fix / 100) / buy12, a)
fix3 = round((usdt123 + usdt123 * koef_fix / 100) / buy123, a)
fix4 = round((usdt1234 + usdt1234 * koef_fix / 100) / buy1234, a)
fix5 = round((usdt12345 + usdt12345 * koef_fix / 100) / buy12345, a)
print('prices for sell-limit:', fix1, fix2, fix3, fix4, fix5)
