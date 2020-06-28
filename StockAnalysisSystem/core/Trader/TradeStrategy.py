import pandas as pd
from .Interface import IMarket, IBroker


class Trader(IMarket.Observer):
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
        print('---------------------------------------- on_before_trading ----------------------------------------')
        print(price_history)

    def on_call_auction(self, price_board: dict, *args, **kwargs):
        print('==========> on_call_auction')
        print(price_board)

    def on_trading(self, price_board: dict, *args, **kwargs):
        print('----------> on_trading')
        print(price_board)

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        print('---------------------------------------- on_after_trading ----------------------------------------')
        print(price_history)






















