import pandas as pd
from .Sizer import *
from .Interface import IMarket, IBroker, Order


class Trader(IMarket.Observer, Order.Observer):
    def __init__(self, market: IMarket, broker: IBroker):
        self.__market = market
        self.__broker = broker
        super(Trader, self).__init__()

    # -------------------------------------------------------------------------------------------

    def market(self) -> IMarket:
        return self.__market

    def broker(self) -> IBroker:
        return self.__broker

    # ------------------------------ Interface of IMarket.Observer ------------------------------

    def level(self) -> int:
        return 5

    def on_prepare_trading(self, securities: [], *args, **kwargs):
        for security in securities:
            self.market().watch_security(security, self)

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        # print('---------------------------------------- on_before_trading ----------------------------------------')
        # print(price_history)
        pass

    def on_call_auction(self, price_board: dict, *args, **kwargs):
        # print('==========> on_call_auction')
        # print(price_board)
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        # print('----------> on_trading')
        # print(price_board)
        pass

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        print('---------------------------------------- on_after_trading ----------------------------------------')
        print(price_history)

    # ------------------------------ Interface of Order.Observer ------------------------------

    def on_order_status_updated(self, order: Order, prev_status: int):
        pass


class GridTrader(Trader):
    def __init__(self, market: IMarket, broker: IBroker,
                 security: str, upper_pct: float, lower_pct: float):
        self.__base = None
        self.__security = security
        self.__upper_pct = upper_pct
        self.__lower_pct = lower_pct
        super(GridTrader, self).__init__(market, broker)

    # ------------------------------ Interface of IMarket.Observer ------------------------------

    def level(self) -> int:
        return 5

    def on_prepare_trading(self, securities: [], *args, **kwargs):
        self.market().watch_security(self.__security, self)

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        order = self.broker().buy_market(self.__security, BuyPositionPercent(10))
        order.watch(self)

    def on_call_auction(self, price_board: dict, *args, **kwargs):
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        pass

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        pass

    # ------------------------------ Interface of Order.Observer ------------------------------

    def on_order_status_updated(self, order: Order, prev_status: int):
        if order.status() == Order.STATUS_COMPLETED:
            if self.__base is None:
                self.__base = order.price




















