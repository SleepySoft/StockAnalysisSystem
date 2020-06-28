import pandas as pd


class IMarket:
    class Observer:
        LEVEL_FIRST = 0
        LEVEL_NORMAL = 5
        LEVEL_LAST = 10

        def __init__(self):
            pass

        def level(self) -> int:
            pass

        def on_prepare_trading(self, securities: [], *args, **kwargs):
            pass

        def on_before_trading(self, price_history: dict, *args, **kwargs):
            pass

        def on_call_auction(self, price_board: dict, *args, **kwargs):
            pass

        def on_trading(self, price_board: dict, *args, **kwargs):
            pass

        def on_after_trading(self, price_history: dict, *args, **kwargs):
            pass

    def __init__(self):
        pass

    def get_price(self, security: str) -> float:
        pass

    def get_handicap(self, security: str) -> pd.DataFrame:
        pass

    def get_day_limit(self, security: str) -> (float, float):
        pass

    def add_participants(self, observer: Observer):
        pass

    def watch_security(self, security: str, observer: Observer):
        pass

    def unwatch_security(self, security: str, observer: Observer):
        pass


class Order:
    OPERATION_NONE = 0
    OPERATION_BUY_LIMIT = 1
    OPERATION_BUY_MARKET = 2
    OPERATION_SELL_LIMIT = 3
    OPERATION_STOP_LIMIT = 4
    OPERATION_SELL_MARKET = 5

    STATUS_CREATED = 100
    STATUS_SUBMITTED = 101
    STATUS_ACCEPTED = 102
    STATUS_COMPLETED = 103
    STATUS_PARTIAL = 104
    STATUS_REJECTED = 105
    STATUS_CANCELLED = 106
    STATUS_EXPIRED = 107

    def __init__(self, security: str = '', price: float = 0.0, amount: int = 0, operation: int = OPERATION_NONE):
        self.price = price
        self.amount = amount
        self.security = security
        self.operation = operation
        self.order_status = Order.STATUS_CREATED


class IBroker:
    def __init__(self):
        pass

    def buy_limit(self, security: str, price: float, amount: int) -> Order:
        pass

    def buy_market(self, security: str, amount: int) -> Order:
        pass

    def sell_limit(self, security: str, price: float, amount: int) -> Order:
        pass

    def stop_limit(self, security: str, price: float, amount: int) -> Order:
        pass

    def sell_market(self, security: str, amount: int) -> Order:
        pass

    def cancel_order(self, order: Order):
        pass





