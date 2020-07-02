import pandas as pd
import baostock as bs

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


# ------------------------------------------------------- Fields -------------------------------------------------------

FIELDS = {
    'TradeData.Stock.5min': {
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'trade_data_in_day_bao_stock',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

IN_DAY_DATA_FIELDS = 'date,time,code,open,high,low,close,volume,amount,adjustflag'


def __fetch_stock_5min_data(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('trade_date')
        since, until = normalize_time_serial(period, default_since(), today())
        since = max(years_ago(5), since)

        since_txt = date2text(since)
        until_txt = date2text(until)

        bao_code = pickup_bao_code(kwargs)

        lg = bs.login()
        print('login respond error_code:' + lg.error_code)
        print('login respond  error_msg:' + lg.error_msg)

        rs = bs.query_history_k_data_plus(bao_code, IN_DAY_DATA_FIELDS,
                                          start_date=since_txt, end_date=until_txt,
                                          frequency='5', adjustflag='3')
        print('query_history_k_data_plus respond error_code:'+rs.error_code)
        print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        result = pd.DataFrame(data_list, columns=rs.fields)

        bs.logout()

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result['stock_identity'] = result['code'].apply(bao_code_to_stock_identity)
        result['trade_datetime'] = pd.to_datetime(result['time'], format="%Y%m%d%H%M%S%f")
        del result['code']
        del result['date']
        del result['time']

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_stock_5min_data(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS



