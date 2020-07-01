import datetime
import threading
import pandas as pd
from .Interface import IMarket
from ..Utiltity.df_utility import *
from ..Utiltity.time_utility import *
from ..DataHubEntry import DataHubEntry


# -------------------------------------------------- class MarketBase --------------------------------------------------

class MarketBase(IMarket):
    def __init__(self):
        self.__observers = {}
        super(MarketBase, self).__init__()

    # ----------------------------------- Interface of IMarket -----------------------------------

    def get_price(self, security: str) -> float:
        pass

    def get_daily(self, security: str, offset: int = -1) -> dict:
        pass

    def get_handicap(self, security: str) -> pd.DataFrame:
        pass

    def get_day_limit(self, security: str) -> (float, float):
        pass

    def add_participants(self, observer: IMarket.Observer):
        if observer not in self.__observers.keys():
            self.__observers[observer] = []

    def watch_security(self, security: str, observer: IMarket.Observer):
        if observer not in self.__observers.keys():
            self.__observers[observer] = []
        self.__observers[observer].append(security)

    def unwatch_security(self, security: str, observer: IMarket.Observer):
        if observer in self.__observers.keys():
            if security in self.__observers[observer]:
                self.__observers[observer].remove(security)

    # --------------------------------- Observer and Notification --------------------------------

    def get_observer_watch_securities(self, observers: IMarket.Observer) -> [str]:
        return self.__observers.get(observers, [])

    def trigger_prepare_trading(self, securities: [], *args, **kwargs):
        for observer in sorted(self.__observers.keys(), key=lambda ob: ob.level()):
            observer.on_prepare_trading(securities, *args, **kwargs)

    def trigger_before_trading(self, price_history: dict, *args, **kwargs):
        for observer in sorted(self.__observers.keys(), key=lambda ob: ob.level()):
            sub_price_history = self.__get_sub_data_for_observer(observer, price_history)
            observer.on_before_trading(sub_price_history, *args, **kwargs)

    def trigger_call_auction(self, price_board: dict, *args, **kwargs):
        for observer in sorted(self.__observers.keys(), key=lambda ob: ob.level()):
            sub_price_board = self.__get_sub_data_for_observer(observer, price_board)
            observer.on_call_auction(sub_price_board, *args, **kwargs)

    def trigger_trading(self, price_board: dict, *args, **kwargs):
        for observer in sorted(self.__observers.keys(), key=lambda ob: ob.level()):
            sub_price_board = self.__get_sub_data_for_observer(observer, price_board)
            observer.on_trading(sub_price_board, *args, **kwargs)

    def trigger_after_trading(self, price_history: dict, *args, **kwargs):
        for observer in sorted(self.__observers.keys(), key=lambda ob: ob.level()):
            sub_price_history = self.__get_sub_data_for_observer(observer, price_history)
            observer.on_after_trading(sub_price_history, *args, **kwargs)

    def __get_sub_data_for_observer(self, observer: IMarket.Observer, full_data: dict) -> dict:
        if not isinstance(full_data, dict):
            return {}
        # Why not give him all
        return full_data
        # watch_securities = self.get_observer_watch_securities(observer)
        # sub_data = {security: full_data[security] for security in watch_securities}
        # return sub_data


# ---------------------------------------------- class MarketBackTesting -----------------------------------------------

class MarketBackTesting(MarketBase, threading.Thread):
    def __init__(self, data_hub, since: datetime.datetime, until: datetime.datetime):
        self.__data_hub = data_hub

        self.__since = since
        self.__until = until

        self.__daily_data_cache = {}
        self.__serial_data_cache = {}
        self.__cached_securities = []

        # Current price
        self.__price_table = {}
        # The daily
        self.__daily_table = {}
        # Today limit table
        self.__price_limit = {}

        super(MarketBackTesting, self).__init__()

    # ----------------------------- Interface of MarketBase -----------------------------
    def get_price(self, security: str) -> float:
        return self.__price_table.get(security, 0.0)

    def get_daily(self, security: str, offset: int = -1) -> dict:
        daily_data = self.__daily_table.get(security, None)
        if daily_data is None or daily_data.empty:
            return {}
        select_daily_data = daily_data.iloc[offset]
        return select_daily_data.to_dict()

    def get_handicap(self, security: str) -> pd.DataFrame:
        return None

    def get_day_limit(self, security: str) -> (float, float):
        return self.__price_limit.get(security, (0.0, 0.0))

    def watch_security(self, security: str, observer: IMarket.Observer):
        if security not in self.__cached_securities:
            if not self.check_load_back_testing_data(security):
                print('Watch security %s fail.', security)
                return
        super(MarketBackTesting, self).watch_security(security, observer)

    # ----------------------------- Interface of threading ------------------------------

    def run(self):
        self.back_testing_entry()

    # ----------------------------------------------------------------------------------

    def back_testing_entry(self):
        self.trigger_prepare_trading(self.__cached_securities)

        if len(self.__cached_securities) == 0:
            print('No data for back testing.')
            return
        baseline = self.__cached_securities[0]
        baseline_daily = self.__daily_data_cache.get(baseline)

        self.__daily_table.clear()
        for index in list(baseline_daily.index):        # baseline_daily.index.values.tolist():
            if len(self.__daily_table) == 0:
                self.__daily_table = self.__build_daily_test_data(index)
                continue
            print('| ' + str(index) + '------------------------------------------')
            self.back_testing_daily(index)

            print('> Day end')
            for security in self.__daily_table.keys():
                daily_data = self.__daily_table.get(security)
                if not daily_data.empty:
                    select_daily_data = daily_data.iloc[-1]
                    print('%s: [%.2f, %.2f]' % (security, select_daily_data['low'], select_daily_data['high']))

    def back_testing_daily(self, limit: any):
        self.update_day_price_limit()

        self.trigger_before_trading(self.__daily_table)

        self.back_testing_serial(limit)
        self.__daily_table = self.__build_daily_test_data(limit)

        self.trigger_after_trading(self.__daily_table)

    def back_testing_serial(self, limit: any):
        if limit is None:
            # If no limit specified, use the whole serial data for back testing
            back_testing_serial_data = self.__serial_data_cache
        else:
            back_testing_serial_data = self.__build_serial_test_data(limit)

        # # TODO: observer.on_call_auction()
        # if len(back_testing_serial_data) > 0:
        #     self.trigger_trading(back_testing_serial_data)

    def __build_daily_test_data(self, limit: any) -> dict:
        back_testing_data = {}
        for security in self.__daily_data_cache:
            df = self.__daily_data_cache[security]
            df = df[df.index <= limit]
            back_testing_data[security] = df
            if not df.empty:
                self.__price_table[security] = df.iloc[-1]['close']
        return back_testing_data

    def __build_serial_test_data(self, limit: any) -> dict:
        limit = to_py_datetime(limit)
        if limit is None:
            # Currently only supports datetime limit
            return {}

        lower = limit.replace(hour=0, minute=0, second=0)
        upper = limit.replace(hour=23, minute=59, second=59)

        back_testing_serial_data = {}
        for security in self.__serial_data_cache:
            df = self.__serial_data_cache[security]
            if df is None:
                continue
            df_sliced = df[lower <= df.index <= upper]
            if not df_sliced.empty:
                back_testing_serial_data[security] = df_sliced
        return back_testing_serial_data

    def load_back_testing_data(self, security: str, baseline: bool = False):
        daily_data = self.__data_hub.get_data_center().query(
            'TradeData.Stock.Daily', security, (self.__since, self.__until),
            fields=['trade_date', 'open', 'close', 'high', 'low', 'vol'])
        if daily_data is not None and not daily_data.empty:
            daily_data = daily_data.set_index('trade_date', drop=True)
            daily_data['volume'] = daily_data['vol']
            del daily_data['vol']
        else:
            daily_data = None

        # TODO: Serial Data
        serial_data = None
        if serial_data is None or serial_data.empty:
            serial_data = None

        return self.add_back_testing_data(security, daily_data, serial_data, baseline)

    def add_back_testing_data(self, security: str, daily_data: pd.DataFrame or None,
                              serial_data: pd.DataFrame or None, baseline=False) -> bool:
        if not self.check_back_testing_data(daily_data, serial_data):
            return False

        daily_data, serial_data = self.pre_process_back_testing_data(daily_data, serial_data)

        if security in self.__cached_securities:
            self.__cached_securities.remove(security)
        if not baseline:
            self.__cached_securities.append(security)
        else:
            self.__cached_securities.insert(0, security)
        if security not in self.__daily_data_cache.keys():
            self.__daily_data_cache[security] = daily_data
        if security not in self.__serial_data_cache.keys():
            self.__serial_data_cache[security] = serial_data
        return True

    # -----------------------------------------------------------------------------

    def check_load_back_testing_data(self, security: str) -> bool:
        if security not in self.__cached_securities:
            return self.load_back_testing_data(security, False)
        else:
            return True

    def update_day_price_limit(self):
        self.__price_limit.clear()
        for s in self.__daily_table:
            daily_data = self.__daily_table.get(s, None)
            if daily_data is None or len(daily_data) == 0:
                continue
            last_daily_data = daily_data.iloc[-1]
            self.__price_limit[s] = (last_daily_data['lower_limit'], last_daily_data['upper_limit'])

    @staticmethod
    def check_back_testing_data(daily_data: pd.DataFrame or None, serial_data: pd.DataFrame or None):
        if daily_data is None and serial_data is None:
            return False
        if daily_data is not None and not column_includes(daily_data, ('open', 'close', 'high', 'low', 'volume')):
            print('Daily data should include open, close, high, low, volume column.')
            return False
        if serial_data is not None and not column_includes(serial_data, ('price', 'volume')):
            print('Serial data should include price, volume column.')
            return False
        return True

    @staticmethod
    def pre_process_back_testing_data(daily_data: pd.DataFrame or None,
                                      serial_data: pd.DataFrame or None) -> \
            (pd.DataFrame or None, pd.DataFrame or None):
        if daily_data is not None:
            if 'upper_limit' not in daily_data.columns:
                daily_data['upper_limit'] = daily_data['close'].shift(1)
                daily_data['upper_limit'] = daily_data['upper_limit'] * 1.10
            if 'lower_limit' not in daily_data.columns:
                daily_data['lower_limit'] = daily_data['close'].shift(1)
                daily_data['lower_limit'] = daily_data['lower_limit'] * 0.90
            daily_data = daily_data.round({'upper_limit': 2, 'lower_limit': 2})
            daily_data = daily_data.fillna(0.0)
        if serial_data is not None:
            pass
        return daily_data, serial_data

