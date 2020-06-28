import pandas as pd
from .Interface import IMarket, IBroker, Order


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


class Broker(IBroker, IMarket.Observer):
    def __init__(self, market: IMarket):
        self.__market = market

        self.__commission_min = 5.0
        self.__commission_pct = 0.0001

        self.__sort_sell_enable = False

        # Temporary storage complete order
        self.__complete_order = []

        self.__pending_order = []
        self.__finished_order = []
        self.__position = Position()

        super(Broker, self).__init__()

    def get_market(self) -> IMarket:
        return self.__market

    # ------------------------------------- Buy / Sell -------------------------------------

    def buy_limit(self, security: str, price: float, amount: int) -> Order:
        order = Order(security, price, amount, Order.OPERATION_BUY_LIMIT)
        self.check_add_order(order)

    def buy_market(self, security: str, amount: int) -> Order:
        order = Order(security, 0.0, amount, Order.OPERATION_BUY_MARKET)
        self.check_add_order(order)

    def sell_limit(self, security: str, price: float, amount: int) -> Order:
        order = Order(security, price, amount, Order.OPERATION_SELL_LIMIT)
        self.check_add_order(order)

    def stop_limit(self, security: str, price: float, amount: int) -> Order:
        order = Order(security, price, amount, Order.OPERATION_STOP_LIMIT)
        self.check_add_order(order)

    def sell_market(self, security: str, amount: int) -> Order:
        order = Order(security, 0.0, amount, Order.OPERATION_SELL_MARKET)
        self.check_add_order(order)

    def cancel_order(self, order: Order):
        if order in self.__pending_order:
            self.__pending_order.remove(order)
            self.__finished_order.append(order)
            order.order_status = Order.STATUS_CANCELLED

    # ---------------------------------------- Order ---------------------------------------

    def order_valid(self, order: Order) -> bool:
        if order.price < 0 or order.amount <= 0:
            return False
        if order.operation == Order.OPERATION_BUY_LIMIT:
            return order.amount * order.price <= self.__position.cash()
        elif order.operation in [Order.OPERATION_SELL_MARKET, Order.OPERATION_SELL_LIMIT, Order. OPERATION_STOP_LIMIT]:
            return order.amount < self.__position.security_amount(order.security)
        return True

    def check_add_order(self, order: Order):
        if self.order_valid(order):
            order.order_status = Order.STATUS_ACCEPTED
            self.__pending_order.append(order)
        else:
            order.order_status = Order.STATUS_REJECTED
            self.__finished_order.append(order)

    def process_complete_order(self):
        for order in self.__complete_order:
            self.__pending_order.remove(order)
        self.__finished_order.extend(self.__complete_order)
        self.__complete_order.clear()

    def get_pending_orders(self) -> [Order]:
        return self.__pending_order

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

    def on_prepare_trading(self, securities: [], *args, **kwargs):
        for security in securities:
            self.get_market().watch_security(security, self)

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        # TODO: TBD
        pass

    def on_call_auction(self, price_table: pd.DataFrame, *args, **kwargs):
        # TODO: TBD
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        for order in self.__pending_order:
            price = price_board.get(order.security, None)
            if price is None:
                continue
            if self.__order_matchable_in_trading(order, price):
                self.__execute_order_trade(order, price)
        self.process_complete_order()

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        price_brief = {}
        for security in price_history.keys():
            df = price_history.get(security, None)
            if df is None or df.empty:
                continue
            latest_row = df.iloc[0]
            price_brief[security] = latest_row

        for order in self.__pending_order:
            day_price = price_brief.get(order.security, None)
            if day_price is None:
                continue
            matchable, at_price = self.__match_order_in_whole_day(order, day_price)
            if matchable:
                self.__execute_order_trade(order, at_price)
            else:
                order.order_status = Order.STATUS_EXPIRED
                self.__complete_order.append(order)
        self.process_complete_order()

        # Clear all orders after the end of a day
        assert len(self.__pending_order) == 0

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
            self.__complete_order.append(order)
        return result

    @staticmethod
    def __order_matchable_in_trading(order: Order, price: float) -> bool:
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

    @staticmethod
    def __match_order_in_whole_day(order: Order, day_price: dict) -> (bool, float):
        if order.operation in [Order.OPERATION_BUY_MARKET, Order.OPERATION_SELL_MARKET]:
            return True, day_price['open']
        elif order.operation == Order.OPERATION_BUY_LIMIT:
            return order.price >= day_price['low'], order.price
        elif order.operation == Order.OPERATION_SELL_LIMIT:
            return order.price <= day_price['high'], order.price
        elif order.operation == Order.OPERATION_STOP_LIMIT:
            return day_price['low'] < order.price, order.price
        return False, 0.0





