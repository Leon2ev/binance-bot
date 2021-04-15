import numpy as np
import decimal

class Parameters():
  def __init__(
    self,
    symbol: str,
    open_price: float,
    first_order_quote: int,
    coefficient_quote: float,
    coefficient_base: float,
    coefficient_fix: float,
    steps: int
  ):
    self.symbol = symbol
    self.open_price = open_price
    self.first_order_quote = first_order_quote
    self.coefficient_quote = coefficient_quote
    self.coefficient_base = coefficient_base
    self.coefficient_fix = coefficient_fix
    self.steps = steps

  def a_magic(self) -> int:
    return abs(decimal.Decimal(str(self.open_price).rstrip('0')).as_tuple().exponent)
  
  def b_magic(self) -> int:
    return int(4 - self.a_magic()) if 4 - self.a_magic() >= 0 else int(0)

  def triger_buy_limit(self) -> float:
    return float(round(self.open_price + self.open_price / 800, self.a_magic()))

  def exponential_coefficient(self, index: int):
    if index == 2:
      return self.coefficient_base * 1 / 100
    elif index == 3:
      return self.coefficient_base * 1.2 / 100
    elif index == 4:
      return self.coefficient_base * 1.5 / 100
    else:
      return self.coefficient_base * 2 / 100

  def buy_limit_quote_volumes(self) -> list:
    volumes = list()
    volume = int(0)
    i = int(1)
    while i <= self.steps:
      if i == 1:
        volume = self.first_order_quote
        volumes.append(volume)
        i += 1
      else:
        volume = int(round(volume * self.coefficient_quote, 0))
        volumes.append(volume)
        i += 1
    return volumes
  
  def buy_limit_price_levels(self) -> list:
    price_levels = list()
    price_level = int(0)
    i = int(1)
    while i <= self.steps:
      if i == 1:
        price_level = self.open_price
        price_levels.append(price_level)
        i += 1
      else:
        exponential = self.exponential_coefficient(i)
        price_level = float(round(price_level - price_level * exponential, self.a_magic()))
        price_levels.append(price_level)
        i += 1
    return price_levels

  def buy_limit_base_volumes(self) -> list:
    volumes = list()
    for quote, price in zip(self.buy_limit_quote_volumes(), self.buy_limit_price_levels()):
      volumes.append(round(quote / price, self.b_magic()))
    return volumes

  def buy_limit_accumulated_quote_volumes(self) -> list:
    return list(np.cumsum(self.buy_limit_quote_volumes()))

  def sell_limit_base_volumes(self) -> list:
    return list(np.cumsum(self.buy_limit_base_volumes()))

  def sell_limit_price_levels(self) -> list:
    price_levels = list()
    for quote, price in zip(self.buy_limit_accumulated_quote_volumes(), self.sell_limit_base_volumes()):
      price_levels.append(round((quote + quote * self.coefficient_fix / 100) / price, self.a_magic()))
    return price_levels

symbol = str('BNBUSDT')
open_price = float(26.38)
first_order_quote = int(20)
coefficient_quote = float(1.2)
coefficient_base = float(1)
coefficient_fix = float(2)
steps = int(5)

test = Parameters(symbol, open_price, first_order_quote, coefficient_quote, coefficient_base, coefficient_fix, steps)
