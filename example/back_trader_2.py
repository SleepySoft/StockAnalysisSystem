# Example from: https://cloud.tencent.com/developer/article/1388272

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import pandas as pd
import backtrader as bt

import StockAnalysisSystem.api as sas_api
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *


# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None

    def notify(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2]:
                    # previous close less than the previous close

                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


if __name__ == '__main__':
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

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # # Create a Data Feed
    # # 本地数据，笔者用Wind获取的东风汽车数据以csv形式存储在本地。
    # # parase_dates = True是为了读取csv为dataframe的时候能够自动识别datetime格式的字符串，big作为index
    # # 注意，这里最后的pandas要符合backtrader的要求的格式
    # dataframe = pd.read_csv('dfqc.csv', index_col=0, parse_dates=True)
    # dataframe['openinterest'] = 0

    data = bt.feeds.PandasData(dataname=df,
                        fromdate = datetime.datetime(2018, 1, 1),
                        todate = datetime.datetime(2019, 12, 31)
                        )
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # Plot the result
    cerebro.plot()


