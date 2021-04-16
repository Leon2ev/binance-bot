from typing import TypedDict, cast
from order_parameters import OrderParameters

class Parameters(TypedDict):
  symbol: str
  open_price: float
  first_order_quote: int
  coefficient_quote: float
  coefficient_base: float
  coefficient_fix: float
  steps: int

parameters: Parameters = dict(
  symbol='ETHBTC',
  open_price=10.38,
  first_order_quote=20,
  coefficient_quote=1.2,
  coefficient_base=1,
  coefficient_fix=2,
  steps=5
)
