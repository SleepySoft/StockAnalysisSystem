from .Interface import IBroker, ISizer


class BuyCashPercent(ISizer):
    def __init__(self, percent: float):
        self.__percent = percent
        super(BuyCashPercent, self).__init__()

    def amount(self, security: str, price: float, broker: IBroker) -> int:
        if price < 0.01:
            return 0
        position = broker.position()
        available_cash = position.cash()
        buy_cash = available_cash * self.__percent / 100
        buy_amount = buy_cash / price
        buy_amount = self.rounding(buy_amount / ISizer.MINIMAL_SHARE) * ISizer.MINIMAL_SHARE
        return buy_amount


class BuyPositionPercent(ISizer):
    def __init__(self, percent: float):
        self.__percent = percent
        super(BuyPositionPercent, self).__init__()

    def amount(self, security: str, price: float, broker: IBroker) -> int:
        if price < 0.01:
            return 0
        position = broker.position()
        available_cash = position.cash()
        security_cash = position.security_amount(security) * price
        total_cash = available_cash + security_cash
        buy_cash = total_cash * self.__percent / 100
        buy_cash = min(buy_cash, available_cash)
        buy_amount = buy_cash / price
        buy_amount = self.rounding(buy_amount / ISizer.MINIMAL_SHARE) * ISizer.MINIMAL_SHARE
        return buy_amount


class SellCashReference(ISizer):
    def __init__(self, ref_cash: float):
        self.__ref_cash = ref_cash
        super(SellCashReference, self).__init__()

    def amount(self, security: str, price: float, broker: IBroker) -> int:
        if price < 0.01:
            return 0
        position = broker.position()
        ref_amount = self.__ref_cash / price
        ref_amount = self.rounding(ref_amount / ISizer.MINIMAL_SHARE) * ISizer.MINIMAL_SHARE
        sell_amount = min(ref_amount, position.security_amount(security))
        return sell_amount


class SellPositionPercent(ISizer):
    def __init__(self, percent: float):
        self.__percent = percent
        super(SellPositionPercent, self).__init__()

    def amount(self, security: str, price: float, broker: IBroker) -> int:
        if price < 0.01:
            return 0
        position = broker.position()
        available_cash = position.cash()
        security_cash = position.security_amount(security) * price
        total_cash = available_cash + security_cash
        sell_cash = total_cash * self.__percent / 100
        sizer = SellCashReference(sell_cash)
        return sizer.amount(security, price, broker)



