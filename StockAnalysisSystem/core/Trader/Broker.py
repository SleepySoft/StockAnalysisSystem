import pandas as pd
from .Interface import *


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


class Position:
    def __init__(self):
        self.__cash = 10000.0
        self.__securities = {}      # Security: Amount

    def cash(self) -> float:
        return self.__cash

    def securities(self) -> dict:
        return self.__securities

    def security_amount(self, security: str) -> int:
        return self.__securities.get(security, 0)

    def trade(self, security: str, amount: int, price: float):
        if security in self.__securities.keys():
            self.__securities[security] += amount
            if self.__securities[security] == 0:
                del self.__securities[security]
        self.__cash += price


class Broker(IMarket.Observer):
    def __init__(self):
        self.__commission_min = 5.0
        self.__commission_pct = 0.0001

        self.__sort_sell_enable = False

        self.__pending_order = []
        self.__finished_order = []
        self.__position = Position()

        super(Broker, self).__init__()

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

    # --------------------------------- Interface IMarket.Observer ---------------------------------

    def level(self) -> int:
        return 1

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        pass

    def on_call_auction(self, price_table: pd.DataFrame, *args, **kwargs):
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        left_order = []
        for order in self.__pending_order:
            price = price_board.get(order.security, None)
            if price is None:
                continue

            # TODO: Check daily price limit
            if order.operation == Order.OPERATION_BUY_MARKET:
                total_price = order.amount * price
                if self.__position.cash() >= total_price:
                    self.__position.trade(order.security, order.amount, -total_price)
                    order.status = Order.STATUS_COMPLETED
            elif order.operation == Order.OPERATION_SELL_MARKET:
                if self.__position.security_amount(order.security) > order.amount:
                    total_price = order.amount * price
                    self.__position.trade(order.security, -order.amount, total_price)
            elif order.operation == Order.OPERATION_BUY_LIMIT:
                total_price = order.amount * price
                if price <= order.price and self.__position.cash() >= total_price:
                    self.__position.trade(order.security, order.amount, -total_price)
                    order.status = Order.STATUS_COMPLETED
            elif order.operation == Order.OPERATION_SELL_LIMIT:
                if price >= order.price and self.__position.security_amount(order.security) > order.amount:
                    total_price = order.amount * price
                    self.__position.trade(order.security, -order.amount, total_price)
                    order.status = Order.STATUS_COMPLETED
            elif order.operation == Order.OPERATION_STOP_LIMIT:
                if price <= order.price and self.__position.security_amount(order.security) > order.amount:
                    total_price = order.amount * price
                    self.__position.trade(order.security, -order.amount, total_price)
                    order.status = Order.STATUS_COMPLETED

            if order.status == Order.STATUS_COMPLETED:
                self.__finished_order.append(order)
            else:
                left_order.append(order)
        self.__pending_order = left_order

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        price_brief = {}
        for security in price_history.keys():
            df = price_history.get(security, None)
            if df is None or df.empty():
                continue
            latest_row = df.iloc[0]
            price_brief[security] = latest_row

        for order in self.__pending_order:
            if order.operation == Order.OPERATION_BUY_MARKET:
                latest_row['open']
            elif order.operation == Order.OPERATION_SELL_MARKET:
                latest_row['open']
            elif order.operation == Order.OPERATION_BUY_LIMIT:
                if order.price >= latest_row['low']:
                    pass
            elif order.operation == Order.OPERATION_SELL_LIMIT:
                if order.price <= latest_row['high']:
                    pass
            elif order.operation == Order.OPERATION_STOP_LIMIT:
                if latest_row['low'] < order.price:
                    pass





