import decimal
from typing import Any

class Orders():
    def __init__(
        self,
        signal
    ):
        for key, value in signal.items():
            setattr(self, key.lower(), value)
            self.step: int = 0
            self.initiated: bool = False
            self.buy_limit_id: int = int()
            self.sell_limit_id: int = int()

    def __getattr__(self, name: str) -> Any: pass

    def a_magic(self) -> int:
        return abs(decimal.Decimal(str(self.open_price).rstrip('0')).as_tuple().exponent)
    
    def b_magic(self) -> int:
        return int(4 - self.a_magic()) if 4 - self.a_magic() >= 0 else int(0)

    def triger_buy_limit(self) -> float:
        return float(round(self.open_price + self.open_price / self.coefficient_set, self.a_magic()))

    def exponential_coefficient(self, index: int):
        return self.coefficient_base/100*(1+index/10)

    def buy_limit_quote_volumes(self) -> list[float]:
        volumes = list()
        volume: float = 0
        i: int = 1

        while i <= self.steps:
            if i == 1:
                volume = self.first_order_quote
                volumes.append(volume)
                i += 1
            else:
                volume = float(round(volume * self.coefficient_quote, 2))
                volumes.append(volume)
                i += 1
        return volumes
    
    def buy_limit_price_levels(self) -> list[float]:
        price_levels = list()
        price_level: float = 0
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

    def cumulative_sum(self, x: list[float]) -> list[float]:
        cum_sum: list = list()
        current: float = 0

        for i in x:
            current = round(current + i, self.b_magic())
            cum_sum.append(current)
        return cum_sum

    def buy_limit_accumulated_quote_volumes(self) -> list[float]:
        return self.cumulative_sum(self.buy_limit_quote_volumes())

    def sell_limit_accumulated_base_volumes(self) -> list[float]:
        return self.cumulative_sum(self.buy_limit_base_volumes())

    def sell_limit_price_levels(self) -> list[float]:
        price_levels = list()

        for quote, price in zip(self.buy_limit_accumulated_quote_volumes(), self.sell_limit_accumulated_base_volumes()):
            price_levels.append(round((quote + quote * self.coefficient_fix / 100) / price, self.a_magic()))
        return price_levels
