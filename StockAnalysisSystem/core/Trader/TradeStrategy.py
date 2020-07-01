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
                 security: str, upper_pct: float, lower_pct: float, trade_step: int):
        self.__security = security
        self.__upper_pct = upper_pct
        self.__lower_pct = lower_pct
        self.__trade_step = trade_step

        # Trade Grid (10% per level with 4 trade step for example):
        #               1.4641
        #               1.331
        #               1.21
        #               1.1     <- Sell order
        #               1.0     <- Current level
        #               0.9     <- Buy order
        #               0.81
        #               0.729
        #               0.6561
        #
        # If sell order complete, the current level will shift -1
        # If buy order complete, the current level will shift 1

        self.__trade_grid = []
        self.__current_level = None

        self.__buy_order = None
        self.__sell_order = None
        super(GridTrader, self).__init__(market, broker)

    # ------------------------------ Interface of IMarket.Observer ------------------------------

    def level(self) -> int:
        return 5

    def on_prepare_trading(self, securities: [], *args, **kwargs):
        self.market().watch_security(self.__security, self)

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        if self.__buy_order is None and self.__sell_order is None:
            self.re_order()

    def on_call_auction(self, price_board: dict, *args, **kwargs):
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        pass

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        pass

    # ------------------------------ Interface of Order.Observer ------------------------------

    def on_order_status_updated(self, order: Order, prev_status: int):
        if order.status() == Order.STATUS_COMPLETED:
            if self.__current_level is None:
                self.build_trade_grid(order.price)
                # It must be the middle of trade grid
                self.__current_level = self.__trade_step
                print('Base decided, price:%.2f, level: %d' % (order.price, self.__current_level))

            if self.__buy_order is not None and self.__buy_order == order:
                self.__current_level += 1
                self.__buy_order = None
                print('Buy  order deal, level increase to %d' % self.__current_level)

            if self.__sell_order is not None and self.__sell_order == order:
                self.__current_level -= 1
                self.__sell_order = None
                print('Sell order deal, level increase to %d' % self.__current_level)

            self.re_order()

        elif order.finished():
            if self.__buy_order == order:
                self.__buy_order = None

            if self.__sell_order == order:
                self.__sell_order = None

    # -----------------------------------------------------------------------------------------

    def re_order(self):
        print('Re-order...')

        if self.__current_level is None:
            print('No base position, create a market price buy order.')
            order = self.broker().buy_market(self.__security, BuyPositionPercent(10))
            order.watch(self)
            return

        if self.__sell_order is not None:
            self.broker().cancel_order(self.__sell_order)
            self.__sell_order = None

        if self.__buy_order is not None:
            self.broker().cancel_order(self.__buy_order)
            self.__buy_order = None

        if self.__current_level - 1 >= 0:
            sell_price = self.__trade_grid[self.__current_level - 1]
            self.__sell_order = self.broker().sell_limit(self.__security, sell_price,
                                                         SellPositionPercent(100.0 / (self.__trade_step * 2 + 1)))
            self.__sell_order.watch(self)

        if self.__current_level + 1 < len(self.__trade_grid):
            buy_price = self.__trade_grid[self.__current_level + 1]
            self.__buy_order = self.broker().buy_limit(self.__security, buy_price,
                                                       BuyPositionPercent(100.0 / (self.__trade_step * 2 + 1)))
            self.__buy_order.watch(self)

    def build_trade_grid(self, base: float):
        self.__trade_grid = [base]
        for i in range(self.__trade_step):
            self.__trade_grid.insert(0, base * pow((100 + self.__upper_pct) / 100, i + 1))
            self.__trade_grid.append(base * pow((100 - self.__lower_pct) / 100, i + 1))
        print('--------------- Trade grid: ---------------')
        print(str(self.__trade_grid))
        print('-------------------------------------------')




















