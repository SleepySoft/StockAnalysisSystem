import pandas as pd
from .Interface import IMarket, IBroker, Position, Order, ISizer


class Broker(IBroker, IMarket.Observer):
    def __init__(self, market: IMarket):
        self.__market = market

        self.__commission_min = 5.0
        self.__commission_pct = 0.0001

        self.__sort_sell_enable = False

        self.__pending_order = []
        self.__finished_order = []
        self.__position = Position()

        super(Broker, self).__init__()

    def market(self) -> IMarket:
        return self.__market

    def position(self) -> Position:
        return self.__position

    # ------------------------------------- Buy / Sell -------------------------------------

    def buy_limit(self, security: str, price: float, size: ISizer) -> Order:
        amount = size.amount(security, price, self) if isinstance(size, ISizer) else size
        order = Order(security, price, amount, Order.OPERATION_BUY_LIMIT)
        self.check_add_order(order)
        return order

    def buy_market(self, security: str, size: ISizer) -> Order:
        amount = size.amount(security, self.market().get_price(security), self) if isinstance(size, ISizer) else size
        order = Order(security, 0.0, amount, Order.OPERATION_BUY_MARKET)
        self.check_add_order(order)
        return order

    def sell_limit(self, security: str, price: float, size: ISizer) -> Order:
        amount = size.amount(security, price, self) if isinstance(size, ISizer) else size
        order = Order(security, price, amount, Order.OPERATION_SELL_LIMIT)
        self.check_add_order(order)
        return order

    def stop_limit(self, security: str, price: float, size: ISizer) -> Order:
        amount = size.amount(security, price, self) if isinstance(size, ISizer) else size
        order = Order(security, price, amount, Order.OPERATION_STOP_LIMIT)
        self.check_add_order(order)
        return order

    def sell_market(self, security: str, size: ISizer) -> Order:
        amount = size.amount(security, self.market().get_price(security), self) if isinstance(size, ISizer) else size
        order = Order(security, 0.0, amount, Order.OPERATION_SELL_MARKET)
        self.check_add_order(order)
        return order

    def cancel_order(self, order: Order):
        if order in self.__pending_order:
            self.__pending_order.remove(order)
            self.__finished_order.append(order)
            order.update_status(Order.STATUS_CANCELLED)

    # ---------------------------------------- Order ---------------------------------------

    def order_valid(self, order: Order) -> bool:
        if order.price < 0 or order.amount <= 0:
            return False
        if order.operation == Order.OPERATION_BUY_LIMIT:
            return order.amount * order.price <= self.__position.cash()
        elif order.operation in [Order.OPERATION_SELL_MARKET, Order.OPERATION_SELL_LIMIT, Order. OPERATION_STOP_LIMIT]:
            return order.amount <= self.__position.security_amount(order.security)
        return True

    def check_add_order(self, order: Order):
        if self.order_valid(order):
            self.__debug('Add :', str(order))
            order.update_status(Order.STATUS_ACCEPTED)
            self.__pending_order.append(order)
        else:
            self.__debug('Drop:', str(order))
            order.update_status(Order.STATUS_REJECTED)
            self.__finished_order.append(order)

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
            self.market().watch_security(security, self)

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        # TODO: TBD
        pass

    def on_call_auction(self, price_board: dict, *args, **kwargs):
        # TODO: TBD
        pass

    def on_trading(self, price_board: dict, *args, **kwargs):
        pending_order = self.__pending_order.copy()
        for order in pending_order:
            price = price_board.get(order.security, None)
            if price is None:
                continue
            if self.__order_matchable_in_trading(order, price):
                result = self.__execute_order_trade(order, price)
                if result:
                    self.__complete_order(order, Order.STATUS_COMPLETED)

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        # price_brief = {}
        # for security in price_history.keys():
        #     df = price_history.get(security, None)
        #     if df is None or df.empty:
        #         continue
        #     latest_row = df.iloc[0]
        #     price_brief[security] = latest_row

        pending_order = self.__pending_order.copy()
        for order in pending_order:
            result = False
            day_price = self.market().get_daily(order.security)
            matchable, at_price = self.__match_order_in_whole_day(order, day_price)
            if matchable:
                result = self.__execute_order_trade(order, at_price)
            self.__complete_order(order, Order.STATUS_COMPLETED if result else Order.STATUS_EXPIRED)

        # # Clear all orders after the end of a day
        # assert len(self.__pending_order) == 0

    def __execute_order_trade(self, order: Order, price: float) -> bool:
        result = False
        if order.operation in [order.OPERATION_BUY_MARKET, order.OPERATION_SELL_MARKET]:
            order.price = price
        if order.operation in [order.OPERATION_BUY_LIMIT, order.OPERATION_BUY_MARKET]:
            result = self.__position.buy(order.security, price, order.amount)
        elif order.operation in [order.OPERATION_SELL_LIMIT, order.OPERATION_SELL_MARKET,
                                 order.OPERATION_STOP_LIMIT]:
            result = self.__position.sell(order.security, price, order.amount)
        if result:
            commission = self.calc_commission(price * order.amount)
            self.__position.cash_out(commission, 'commission')
            self.__debug('Deal:', str(order))
            print(self.__position.statistics(self.market()))
            order.update_status(Order.STATUS_COMPLETED)
        return result

    def __complete_order(self, order: Order, status: int):
        if order in self.__pending_order:
            self.__pending_order.remove(order)
        self.__finished_order.append(order)
        order.update_status(status)

        # for order in self.__complete_order:
        #     self.__pending_order.remove(order)
        # self.__finished_order.extend(self.__complete_order)
        # self.__complete_order.clear()

    def __order_matchable_in_trading(self, order: Order, price: float) -> bool:
        lower_limit, upper_limit = self.market().get_day_limit(order.security)
        reach_lower_limit = (abs(price - lower_limit) < 0.01)
        reach_upper_limit = (abs(price - upper_limit) < 0.01)
        if order.operation == Order.OPERATION_BUY_MARKET:
            return not reach_upper_limit
        if order.operation == Order.OPERATION_SELL_MARKET:
            return not reach_lower_limit
        if order.operation == Order.OPERATION_BUY_LIMIT:
            return order.price >= price and not reach_upper_limit
        if order.operation == Order.OPERATION_SELL_LIMIT:
            return price >= order.price and not reach_lower_limit
        if order.operation == Order.OPERATION_STOP_LIMIT:
            return price <= order.price and not reach_lower_limit
        return False

    def __match_order_in_whole_day(self, order: Order, day_price: dict) -> (bool, float):
        if len(day_price) == 0:
            return False, 0.0

        stay_in_limit = day_price['open'] == day_price['close'] and \
                        day_price['high'] == day_price['low'] and \
                        day_price['low'] == day_price['close']
        if stay_in_limit:
            lower_limit, upper_limit = self.market().get_day_limit(order.security)
            stay_in_lower_limit = day_price['low'] == lower_limit
            stay_in_upper_limit = day_price['high'] == upper_limit
        else:
            stay_in_lower_limit = False
            stay_in_upper_limit = False

        if order.operation == Order.OPERATION_BUY_MARKET:
            return not stay_in_upper_limit, day_price['open']
        if order.operation == Order.OPERATION_SELL_MARKET:
            return not stay_in_lower_limit, day_price['open']
        elif order.operation == Order.OPERATION_BUY_LIMIT:
            return not stay_in_upper_limit and order.price >= day_price['low'], order.price
        elif order.operation == Order.OPERATION_SELL_LIMIT:
            return not stay_in_lower_limit and order.price <= day_price['high'], order.price
        elif order.operation == Order.OPERATION_STOP_LIMIT:
            return not stay_in_lower_limit and day_price['low'] < order.price, order.price
        return False, 0.0

    # ---------------------------------------------------------------------------------

    @staticmethod
    def __debug(*args):
        print(' '.join(args))





