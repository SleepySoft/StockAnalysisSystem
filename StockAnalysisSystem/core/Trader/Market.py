import datetime
import threading
import pandas as pd
from .Interface import IMarket
from ..DataHubEntry import DataHubEntry


class MarketBase(IMarket):
    def __init__(self):
        self.__observers = {}
        super(MarketBase, self).__init__()

    def get_price(self, security: str) -> float:
        pass

    def get_handicap(self, security: str) -> pd.DataFrame:
        pass

    def get_day_limit(self, security: str) -> (float, float):
        pass

    def watch_security(self, security: str, observer: IMarket.Observer):
        if observer not in self.__observers.keys():
            self.__observers[observer] = []
        self.__observers[observer].append(security)

    def unwatch_security(self, security: str, observer: IMarket.Observer):
        if observer in self.__observers.keys():
            if security in self.__observers[observer]:
                self.__observers[observer].remove(security)


class MarketBackTesting(MarketBase, threading.Thread):
    def __init__(self, data_hub, since: datetime.datetime, until: datetime.datetime, datetime_field: str):
        self.__data_hub = data_hub

        self.__base_line_since = since
        self.__base_line_until = until
        self.__base_line_field = datetime_field
        self.__base_line_testing = self.__base_line_since

        self.__daily_cache = {}
        self.__history_cache = {}
        self.__watching_securities = []

        # Current price
        self.__price_table = {}
        # The daily
        self.__daily_table = {}
        self.__history_table = {}

        super(MarketBackTesting, self).__init__()

    # ----------------------------- Interface of MarketBase -----------------------------

    def watch_security(self, security: str, observer: IMarket.Observer):
        if security not in self.__watching_securities:
            if not self.on_watch_security(security):
                print('Watch security %s fail.', security)
                return
        super(MarketBackTesting, self).watch_security(security, observer)

    def get_price(self, security: str) -> float:
        return self.__price_table.get(security, 0.0)

    def get_history(self, security: str) -> pd.DataFrame:
        history = self.__history_cache.get(security, None)
        history = history[history[self.__base_line_field] < self.__base_line_testing]

    def get_day_limit(self, security: str) -> (float, float):
        pass

    # ----------------------------- Interface of threading ------------------------------

    def run(self):
        self.back_testing_entry()

    # ----------------------------------------------------------------------------------

    def back_testing_entry(self):
        pass

    def elapsed(self):
        for observer in sorted(self.__observers.keys(), key=lambda ob: ob.level()):
            observer.on_before_trading()
            observer.on_call_auction()
            observer.on_trading()
            observer.on_after_trading()

    def load_security_data(self, security: str, base_line: bool = False):
        pass

    def add_back_testing_data(self, df: pd.DataFrame, base_line: bool = False):
        pass

    # -----------------------------------------------------------------------------

    def on_watch_security(self, security: str) -> bool:
        # TODO: minutes
        if security not in self.__daily_cache.keys():
            pass

        if security not in self.__history_cache.keys():
            df = self.__data_hub.get_data_center().query(
                'TradeData.Stock.Daily', security, self.__data_since, self.__data_until)
            if df is not None and not df.empty():
                self.__history_cache[security] = df
            else:
                print('Warning: Cannot load daily data of %s for back testing.' % security)



















import pandas as pd


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


class Exchange:
    def __init__(self):
        self.__commission_min = 5.0
        self.__commission_pct = 0.0001

        self.__sort_sell_enable = False

        self.__pending_order = []
        self.__finished_order = []

    # ------------------------------------- Buy / Sell -------------------------------------

    def buy_limit(self, security: str, price: float, amount: int) -> Order:
        order = Order(security, price, amount, Order.OPERATION_BUY_LIMIT)
        self.__pending_order.append(order)
        return order

    def buy_market(self, security: str, amount: int) -> Order:
        order = Order(security, 0.0, amount, Order.OPERATION_BUY_MARKET)
        self.__pending_order.append(order)
        return order

    def sell_limit(self, security: str, price: float, amount: int) -> Order:
        order = Order(security, price, amount, Order.OPERATION_SELL_LIMIT)
        self.__pending_order.append(order)
        return order

    def stop_limit(self, security: str, price: float, amount: int) -> Order:
        order = Order(security, price, amount, Order.OPERATION_STOP_LIMIT)
        self.__pending_order.append(order)
        return order

    def sell_market(self, security: str, amount: int) -> Order:
        order = Order(security, 0.0, amount, Order.OPERATION_SELL_MARKET)
        self.__pending_order.append(order)
        return order

    # ---------------------------------------- Order ---------------------------------------

    def cancel_order(self, order: Order):
        if order in self.__pending_order:
            self.__pending_order.pop(order)
            self.__finished_order.append(order)
            order.order_status = Order.STATUS_CANCELLED

    def get_pending_orders(self) -> [Order]:
        pass

    # ---------------------------------- Trade Data Access ----------------------------------

    def subscribe_security(self):
        pass

    def unsubscribe_security(self):
        pass

    def get_price(self):
        pass

    def get_handicap(self):
        pass

    def get_position(self):
        pass

    # ----------------------------------- Exchange Setting -----------------------------------

    # ------------------- commission -------------------

    def set_commission(self, pct: float, minimum: float):
        self.__commission_pct, self.__commission_min = pct, minimum

    def get_commission(self) -> (float, float):
        return self.__commission_pct, self.__commission_min

    def calc_commission(self, transaction_amount) -> float:
        return max(transaction_amount * self.__commission_pct, self.__commission_min)

    # ------------------- Sort Sell -------------------

    def set_sort_sell_enable(self, enable: bool):
        self.__sort_sell_enable = enable

    def get_sort_sell_enable(self) -> bool:
        return self.__sort_sell_enable






