import math

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

    def get_daily(self, security: str, offset: int = -1) -> dict:
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


class Position:
    def __init__(self):
        self.__cash = 0
        self.__securities = {}  # Security: Amount
        self.__capital_flow = []
        self.__capital_flow_info = []
        self.cash_init(100000.0)

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
        self.trade(security, -amount, price * amount)
        return True

    def trade(self, security: str, amount: int, total_price: float):
        if security in self.__securities.keys():
            self.__securities[security] += amount
            if self.__securities[security] == 0:
                del self.__securities[security]
        else:
            self.__securities[security] = amount
        self.__cash += total_price

    def cash_in(self, cash: float, reason: str):
        self.__cash += cash
        self.__record_capital_flow(cash, reason=reason)

    def cash_out(self, cash: float, reason: str):
        self.__cash -= cash
        self.__record_capital_flow(-cash, reason=reason)

    def cash_init(self, cash: float):
        self.__cash = cash
        self.__reset_capital_flow()
        self.__record_capital_flow(cash, reason='Cash init')

    def statistics(self, market: IMarket) -> str:
        sum_value = self.__cash
        text = ['Position: ',
                '  cash: %0.f' % self.__cash]
        for security in sorted(self.__securities.keys()):
            price = market.get_price(security)
            amount = self.__securities.get(security)
            value = price * amount
            sum_value += value
            text.append('  %s: %.2f * %d = %f' % (security, price, amount, value))
        text.append('Total value: %.2f' % sum_value)
        return '\n'.join(text)

    def total_position(self, market: IMarket) -> float:
        position_sum = self.__cash
        for security in self.__securities.keys():
            price = market.get_price(security)
            position_sum += price * self.__securities.get(security, 0.0)
        return position_sum

    # --------------------------------------------------------------------

    def __reset_capital_flow(self):
        self.__capital_flow.clear()
        self.__capital_flow_info.clear()

    def __record_capital_flow(self, cash: float, **kwargs):
        self.__capital_flow.append(cash)
        self.__capital_flow_info.append(kwargs)


class Order:
    OPERATION_NONE = 0
    OPERATION_BUY_LIMIT = 1
    OPERATION_BUY_MARKET = 2
    OPERATION_SELL_LIMIT = 3
    OPERATION_STOP_LIMIT = 4
    OPERATION_SELL_MARKET = 5

    OPERATION_TEXT_TABLE = {
        OPERATION_NONE:         'NONE       ',
        OPERATION_BUY_LIMIT:    'Buy  Limit ',
        OPERATION_BUY_MARKET:   'Buy Market ',
        OPERATION_SELL_LIMIT:   'Sell Limit ',
        OPERATION_STOP_LIMIT:   'Stop Limit ',
        OPERATION_SELL_MARKET:  'Sell Market',
    }

    STATUS_CREATED = 100
    STATUS_SUBMITTED = 101
    STATUS_ACCEPTED = 102
    STATUS_COMPLETED = 103
    STATUS_PARTIAL = 104
    STATUS_REJECTED = 105
    STATUS_CANCELLED = 106
    STATUS_EXPIRED = 107

    STATUS_TEXT_TABLE = {
        STATUS_CREATED:     'Created',
        STATUS_SUBMITTED:   'Submitted',
        STATUS_ACCEPTED:    'Accepted',
        STATUS_COMPLETED:   'Complete',
        STATUS_PARTIAL:     'Partial',
        STATUS_REJECTED:    'Rejected',
        STATUS_CANCELLED:   'Cancelled',
        STATUS_EXPIRED:     'Expired',
    }

    class Observer:
        def __init__(self):
            pass

        def on_order_status_updated(self, order, prev_status: int):
            pass

    def __init__(self, security: str = '', price: float = 0.0, amount: int = 0, operation: int = OPERATION_NONE):
        self.price = price
        self.amount = amount
        self.security = security
        self.operation = operation

        self.__status = Order.STATUS_CREATED
        self.__observer: Order.Observer = None

    def __str__(self) -> str:
        seperator = '->' if self.is_buy_order() else (
            '<-' if self.is_sell_order() else '--'
        )
        return 'Order [%s] %s %s | Security: %s | Amount: %d | Price: %.2f' % \
               (hex(id(self)), seperator,
                self.OPERATION_TEXT_TABLE.get(self.operation, ''),
                self.security, self.amount, self.price)

    def watch(self, observer: Observer):
        self.__observer = observer

    def status(self) -> int:
        return self.__status

    def finished(self) -> bool:
        return self.__status in [Order.STATUS_COMPLETED, Order.STATUS_REJECTED,
                                 Order.STATUS_CANCELLED, Order.STATUS_EXPIRED]

    def is_buy_order(self) -> bool:
        return self.operation in [Order.OPERATION_BUY_LIMIT, Order.OPERATION_BUY_MARKET]

    def is_sell_order(self) -> bool:
        return self.operation in [Order.OPERATION_SELL_LIMIT, Order.OPERATION_STOP_LIMIT, Order.OPERATION_SELL_LIMIT]

    def update_status(self, status: int):
        if not self.status_valid(status):
            # TODO: Error handling
            assert False
        if status != self.__status:
            prev_status = self.__status
            self.__status = status
            if self.__observer is not None:
                self.__observer.on_order_status_updated(self, prev_status)

    @staticmethod
    def status_valid(status: int) -> bool:
        return status in Order.STATUS_TEXT_TABLE.keys()

    @staticmethod
    def operation_valid(operation: int) -> bool:
        return operation in Order.OPERATION_TEXT_TABLE.keys()


class ISizer:
    MINIMAL_SHARE = 100

    ROUND_CLOSE = round
    ROUND_NO_MORE = math.floor
    ROUND_NO_LESS = math.ceil

    def __init__(self, rounding=ROUND_CLOSE):
        self.__rounding = rounding

    def amount(self, security: str, price: float, broker) -> int:
        pass

    def rounding(self, x: any) -> any:
        return self.__rounding(x)


class IBroker:
    def __init__(self):
        pass

    def market(self) -> IMarket:
        pass

    def position(self) -> Position:
        pass

    def buy_limit(self, security: str, price: float, size: ISizer) -> Order:
        pass

    def buy_market(self, security: str, size: ISizer) -> Order:
        pass

    def sell_limit(self, security: str, price: float, size: ISizer) -> Order:
        pass

    def stop_limit(self, security: str, price: float, size: ISizer) -> Order:
        pass

    def sell_market(self, security: str, size: ISizer) -> Order:
        pass

    def cancel_order(self, order: Order):
        pass





