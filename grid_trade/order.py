from typing import Any

from binance.helpers import round_step_size


class Order():
    def __init__(
        self,
        parameters,
        backup: bool = False
    ):

        '''Order class keeps all the information related to current trading pair state
        and make calculaition of next possible orders depends on which parameters user
        provides. 
        
        Argument "parameters" set by user is used to define trading parameters like
        price levels and amount that should be traded on this levels.
        
        If "backup" is set to True that means that "parameters" was taken from the backup.
        In this case they will contain more data, like placed orderID and current step if
        user using grids for trading. "This is made to keep state for each trade when 
        server restart.'''

        if backup:
            for key, value in parameters.items():
                setattr(self, key.lower(), value)
        else:
            for key, value in parameters.items():
                setattr(self, key.lower(), value)
                self.tick_size: float = float()
                self.step_size: float = float()
                self.step: int = int()
                self.initiated: bool = False
                self.buy_limit_id: int = int()
                self.sell_limit_id: int = int()


    def __getattr__(self, name: str) -> Any: pass


    def triger_buy_limit(self) -> float:
        return self.open_price + self.open_price / self.coefficient_set


    def coefficient_grow(self, index: int) -> float:
        return self.coefficient_base / 100 * (1 + index / 10)


    def quote_amount(self) -> list[float]:
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


    def buy_level(self) -> list[float]:
        price_levels: list[float] = list()
        price_level: float = float()
        i: int = int(1)

        while i <= self.steps:

            if i == 1:
                price_level = self.open_price
                price_levels.append(price_level)
                i += 1
            else:
                exponential = self.coefficient_grow(i)
                price_level = round_step_size(price_level - price_level * exponential, self.tick_size)
                price_levels.append(price_level)
                i += 1

        return price_levels


    def buy_quantity(self) -> list[float]:
        volumes: list[float] = list()

        for quote, price in zip(
            self.quote_amount(),
            self.buy_level()
            ):
                amount = round_step_size(quote / price, self.step_size)
                volumes.append(amount)

        return volumes


    def cumulative_sum(self, x: list[float]) -> list[float]:
        cum_sum: list[float] = list()
        current: float = float()

        for i in x:
            current = round_step_size(current + i, self.step_size)
            cum_sum.append(current)

        return cum_sum


    def cumulative_quote(self) -> list[float]:
        return self.cumulative_sum(self.quote_amount())


    def sell_quantity(self) -> list[float]:
        return self.cumulative_sum(self.buy_quantity())


    def sell_level(self) -> list[float]:
        price_levels: list[float] = list()

        for quote, quantity in zip(
            self.cumulative_quote(),
            self.sell_quantity()
            ):
                price_level = round_step_size((quote + quote * self.coefficient_fix / 100) / quantity, self.tick_size)
                price_levels.append(price_level)

        return price_levels
