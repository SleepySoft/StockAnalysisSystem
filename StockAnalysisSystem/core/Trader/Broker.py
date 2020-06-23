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
    
    def buy(self, security: str, price: float, amount: int) -> bool:
        total_price = price * amount
        if amount == 0 or self.__cash < total_price:
            return False
        self.trade(security, amount, -total_price)
        return True

    def sell(self, security: str, price: float, amount: int) -> bool:
        if self.security_amount(security) < amount:
            return False
        self.trade(security, amount, price * amount)
        return True

    def trade(self, security: str, amount: int, total_price: float):
        if security in self.__securities.keys():
            self.__securities[security] += amount
            if self.__securities[security] == 0:
                del self.__securities[security]
        self.__cash += total_price


class Broker(IMarket.Observer):
    def __init__(self):
        self.__commission_min = 5.0
        self.__commission_pct = 0.0001

        self.__sort_sell_enable = False

        # Temporary storage un-trade order
        self.__left_order = []

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
        # TODO: TBD
        pass

    def on_call_auction(self, price_table: pd.DataFrame, *args, **kwargs):
        # TODO: TBD
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        self.__left_order = []
        for order in self.__pending_order:
            price = price_board.get(order.security, None)
            if price is None:
                continue
            if self.__order_matchable_in_trading(order, price):
                self.__execute_order_trade(order, price)
        self.__pending_order = self.__left_order
        self.__left_order = []

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        price_brief = {}
        for security in price_history.keys():
            df = price_history.get(security, None)
            if df is None or df.empty():
                continue
            latest_row = df.iloc[0]
            price_brief[security] = latest_row

        self.__left_order = []
        for order in self.__pending_order:
            day_price = price_brief.get(order.security, None)
            if day_price is None:
                continue
            matchable, at_price = self.__match_order_in_whole_day(order, day_price)
            if matchable:
                self.__execute_order_trade(order, at_price)
        self.__pending_order = self.__left_order
        self.__left_order = []

    def __execute_order_trade(self, order: Order, price: float) -> bool:
        result = False
        if order.operation in [order.OPERATION_BUY_LIMIT, order.OPERATION_BUY_MARKET]:
            result = self.__position.buy(order.security, price, order.amount)
        elif order.operation in [order.OPERATION_SELL_LIMIT, order.OPERATION_SELL_MARKET,
                                 order.OPERATION_STOP_LIMIT]:
            result = self.__position.sell(order.security, price, order.amount)
        if result:
            commission = self.calc_commission(price * order.amount)
            self.__position.trade('commission', 1, -commission)

            order.status = Order.STATUS_COMPLETED
            self.__finished_order.append(order)
        else:
            self.__left_order.append(order)
        return result

    def __order_matchable_in_trading(self, order: Order, price: float) -> bool:
        # TODO: Daily limit
        if order.operation in [Order.OPERATION_BUY_MARKET, Order.OPERATION_SELL_MARKET]:
            return True
        if order.operation == Order.OPERATION_BUY_LIMIT:
            return order.price >= price
        if order.operation == Order.OPERATION_SELL_MARKET:
            return price >= order.price
        if order.operation == Order.OPERATION_STOP_LIMIT:
            return price <= order.price
        return False

    def __match_order_in_whole_day(self, order: Order, day_price: dict) -> (bool, float):
        if order.operation in [Order.OPERATION_BUY_MARKET, Order.OPERATION_SELL_MARKET]:
            return True, day_price['open']
        elif order.operation == Order.OPERATION_BUY_LIMIT:
            return order.price >= day_price['low'], order.price
        elif order.operation == Order.OPERATION_SELL_LIMIT:
            return order.price <= day_price['high'], order.price
        elif order.operation == Order.OPERATION_STOP_LIMIT:
            return day_price['low'] < order.price, order.price
        return False, 0.0





