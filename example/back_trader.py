import os
import sys
import traceback
import pandas as pd
import backtrader as bt

import StockAnalysisSystem.api as sas_api
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *


class StrategyGrid(bt.Strategy):
    grid_base = None
    grid_current = None
    trade_price = None

    def __init__(self):
        self.order = None
        self.dataclose = self.datas[0].close

    def notify(self, order):
        if order.status == order.Completed:
            self.grid_current = self.trade_price

    def next(self):
        current_price = self.dataclose[0]
        if self.grid_base is None:
            self.grid_base = current_price
            self.grid_current = current_price
        if current_price > self.grid_current and current_price / self.grid_current > 1.1:
            self.order = self.sell()
        elif current_price < self.grid_current and current_price / self.grid_current < 0.9:
            self.order = self.buy()
        self.trade_price = current_price


def main():
    project_path = os.path.dirname(os.path.abspath(__file__))

    sas_api.config_set('NOSQL_DB_HOST', 'localhost')
    sas_api.config_set('NOSQL_DB_PORT', '27017')
    sas_api.config_set('TS_TOKEN', 'xxxxxxxxxxxx')

    if not sas_api.init(project_path, True):
        print('sas init fail.')
        print('\n'.join(sas_api.error_log()))
        quit(1)

    stock_identity = '000001.SZSE'
    period = (years_ago(5), now())

    df = sas_api.get_data_center().query('TradeData.Stock.Daily', stock_identity, period)
    if df is None or df.empty:
        print('No data.')
        exit(2)
    df.set_index('trade_date', drop=True, inplace=True)
    df['openinterest'] = 0
    df['volume'] = df['vol']

    cerebro = bt.Cerebro()

    data = bt.feeds.PandasData(dataname=df,
                               fromdate=period[0],
                               todate=period[1]
                               )
    cerebro.adddata(data)

    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    cerebro.broker.set_cash(100000)
    cerebro.addstrategy(StrategyGrid)

    results = cerebro.run()
    print(results)

    cerebro.plot()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass



