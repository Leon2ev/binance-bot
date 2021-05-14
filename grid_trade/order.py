from typing import Any

from binance.helpers import round_step_size


class Order():
    def __init__(
        self,
        parameters
    ):
        for key, value in parameters.items():
            setattr(self, key.lower(), value)
            self.tick_size: float = float()
            self.step_size: float = float()
            self.step: int = int(0)
            self.initiated: bool = False
            self.buy_limit_id: int = int()
            self.sell_limit_id: int = int()


    def __getattr__(self, name: str) -> Any: pass


    def triger_buy_limit(self) -> float:
        return self.open_price + self.open_price / self.coefficient_set


    def exponential_coefficient(self, index: int) -> float:
        return self.coefficient_base / 100 * (1 + index / 10)


    def buy_limit_quote_volumes(self) -> list[float]:
        volumes: list[float] = list()
        volume: float = float()
        i: int = int(1)

        while i <= self.steps:

            if i == 1:
                volume = self.first_order_quote
                volumes.append(volume)
                i += 1
            else:
                volume = volume * self.coefficient_quote
                volumes.append(volume)
                i += 1

        return volumes


    def buy_limit_price_levels(self) -> list[float]:
        price_levels: list[float] = list()
        price_level: float = float()
        i: int = int(1)

        while i <= self.steps:

            if i == 1:
                price_level = self.open_price
                price_levels.append(price_level)
                i += 1
            else:
                exponential = self.exponential_coefficient(i)
                price_level = round_step_size(price_level - price_level * exponential, self.tick_size)
                price_levels.append(price_level)
                i += 1

        return price_levels


    def buy_limit_base_volumes(self) -> list[float]:
        volumes: list[float] = list()

        for quote, price in zip(
            self.buy_limit_quote_volumes(),
            self.buy_limit_price_levels()
            ):
                amount = round_step_size(quote / price, self.tick_size)
                volumes.append(amount)

        return volumes


    def cumulative_sum(self, x: list[float]) -> list[float]:
        cum_sum: list[float] = list()
        current: float = float()

        for i in x:
            current = round_step_size(current + i, self.tick_size)
            cum_sum.append(current)

        return cum_sum


    def buy_limit_accumulated_quote_volumes(self) -> list[float]:
        return self.cumulative_sum(self.buy_limit_quote_volumes())


    def sell_limit_accumulated_base_volumes(self) -> list[float]:
        return self.cumulative_sum(self.buy_limit_base_volumes())


    def sell_limit_price_levels(self) -> list[float]:
        price_levels: list[float] = list()

        for quote, price in zip(
            self.buy_limit_accumulated_quote_volumes(),
            self.sell_limit_accumulated_base_volumes()
            ):
                price_level = round_step_size((quote + quote * self.coefficient_fix / 100) / price, self.step_size)
                price_levels.append(price_level)

        return price_levels
