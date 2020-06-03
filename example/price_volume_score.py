import os
import sys
import traceback
import pandas as pd

import StockAnalysisSystem.api as sas_api
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *


def score_function(price: float, prev_price: float, amount: float, prev_amount: float) -> int:
    EQUAL = 0
    LARGER = 1
    SMALLER = -1

    def compare(a, b) -> int:
        if abs(a - b) / abs(b) < 0.01:
            return EQUAL
        return LARGER if a > b else SMALLER

    # NAN
    if price == 0 or prev_price == 0 or amount == 0 or prev_amount == 0:
        return 0

    price_compare = compare(price, prev_price)
    amount_compare = compare(amount, prev_amount)

    return {
        # Price, Amount
        (LARGER, LARGER): 2,
        (SMALLER, LARGER): 1,
        (EQUAL, EQUAL): 0,
        (SMALLER, SMALLER): -1,
        (SMALLER, LARGER): -2,
    }.get((price_compare, amount_compare), 0)


def calc_stock_trade_score(df: pd.DataFrame, price_field: str, amount_field: str, score_field: str = 'score'):
    if not column_includes(df, [price_field, amount_field]):
        print('calc_stock_trade_score() - Price and Amount field missing.')
        return

    df['prev_price'] = df[price_field].shift(1).fillna(0)
    df['prev_amount'] = df[amount_field].shift(1).fillna(0)
    df[score_field] = df.apply(lambda row: score_function(row[price_field], row['prev_price'],
                                                          row[amount_field], row['prev_amount']), axis=1)


def main():
    offline = True
    project_path = os.path.dirname(os.path.abspath(__file__))

    sas_api.config_set('NOSQL_DB_HOST', 'localhost')
    sas_api.config_set('NOSQL_DB_PORT', '27017')
    sas_api.config_set('TS_TOKEN', 'xxxxxxxxxxxx')

    clock = Clock()
    if not sas_api.init(project_path, True):
        print('sas init fail.')
        print('\n'.join(sas_api.error_log()))
        quit(1)

    stock_list = sas_api.get_data_utility().get_stock_identities()
    if len(stock_list) == 0:
        sas_api.get_data_center().update_local_data('Market.SecuritiesInfo')
        sas_api.get_data_utility().refresh_cache()
        stock_list = sas_api.get_data_utility().get_stock_identities()
    if len(stock_list) == 0:
        print('Cannot get stock list.')
        quit(1)

    score_dict = {}
    for stock_identity in stock_list:
        if offline:
            df = sas_api.get_data_center().query('TradeData.Stock.Daily',
                                                 stock_identity, (days_ago(60), now()))
        else:
            df = sas_api.get_data_center().query_from_plugin('TradeData.Stock.Daily',
                                                             stock_identity, (days_ago(60), now()))

        if df is None or len(df) == 0:
            print('No data for %s' % stock_identity)
            continue

        # Only keep 2 rows
        df = df[['trade_date', 'close', 'vol']]
        calc_stock_trade_score(df, 'close', 'vol')
        score_dict[stock_identity] = df['score'].sum()

    print('Analysis finished, time spending: %.2fs' % clock.elapsed())
    result = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    print(result)

    print('Process Quit.')


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
