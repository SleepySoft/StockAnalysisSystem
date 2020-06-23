import pandas as pd
from .Interface import IMarket


class Trader(IMarket.Observer):
    def __init__(self):
        super(Trader, self).__init__()

    # ------------------------------ Interface of IMarket.Observer ------------------------------

    def level(self) -> int:
        return 5

    def on_before_trading(self, price_history: dict, *args, **kwargs):
        print('---------------------------------------- on_before_trading ----------------------------------------')
        print(price_history)

    def on_call_auction(self, price_table: pd.DataFrame, *args, **kwargs):
        print('==========> on_call_auction')
        print(price_table)

    def on_trading(self, price_board: dict, *args, **kwargs):
        print('----------> on_trading')
        print(price_board)

    def on_after_trading(self, price_history: dict, *args, **kwargs):
        print('---------------------------------------- on_after_trading ----------------------------------------')
        print(price_history)






















