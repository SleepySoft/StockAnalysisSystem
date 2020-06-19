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






