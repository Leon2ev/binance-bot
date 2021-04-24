import numpy as np
import decimal
from typing import Any, TypedDict

class Signal(TypedDict):
  SYMBOL: str
  OPEN_PRICE: float
  FIRST_ORDER_QUOTE: int
  COEFFICIENT_QUOTE: float
  COEFFICIENT_BASE: float
  COEFFICIENT_FIX: float
  STEPS: int

class Orders():
  def __init__(
    self,
    signal: Signal
  ):
    for key, value in signal.items():
      setattr(self, key.lower(), value)
    self.step: int = 0

  def __getattr__(self, name: str) -> Any: pass

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

  def buy_limit_quote_volumes(self) -> list[int]:
    volumes = list()
    volume: int = 0
    i: int = 1
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
  
  def buy_limit_price_levels(self) -> list[float]:
    price_levels = list()
    i: int = 1
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

  def buy_limit_base_volumes(self) -> list[float]:
    volumes = list()
    for quote, price in zip(self.buy_limit_quote_volumes(), self.buy_limit_price_levels()):
      volumes.append(round(quote / price, self.b_magic()))
    return volumes

  def buy_limit_accumulated_quote_volumes(self) -> list[int]:
    return list(np.cumsum(self.buy_limit_quote_volumes()))

  def sell_limit_accumulated_base_volumes(self) -> list[float]:
    return list(np.cumsum(self.buy_limit_base_volumes()))

  def sell_limit_price_levels(self) -> list[float]:
    price_levels = list()
    for quote, price in zip(self.buy_limit_accumulated_quote_volumes(), self.sell_limit_accumulated_base_volumes()):
      price_levels.append(round((quote + quote * self.coefficient_fix / 100) / price, self.a_magic()))
    return price_levels
