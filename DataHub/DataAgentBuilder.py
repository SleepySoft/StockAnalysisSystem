import logging
from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from DataHub.DataAgent import *
except Exception as e:
    sys.path.append(root_path)
    from DataHub.DataAgent import *
finally:
    logger = logging.getLogger('')


def build_data_agent():
    return [
        DataAgent(
            uri='Market.SecuritiesInfo',
            database_entry=None,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field=None,

            query_declare={
                'stock_identity': ([str], [],                   False,  ''),
            },
            result_declare={
                'stock_identity': (['str'], [],                 True,  ''),
                'code':           (['str'], [],                 True,  ''),
                'name':           (['str'], [],                 True,  ''),
                'exchange':       (['str'], [],                 True,  ''),
                'listing_date':   (['datetime'], [],            True,  ''),
            },

            data_duration=DATA_DURATION_NONE,
        ),


    ]

    DECLARE_DATA_AGENT(
        uri='Market.IndexInfo',
        database='StockAnalysisSystem',
        table_prefix='',

        identity_field='stock_identity',
        identity_update_list=None,

        datetime_field=None,
        data_since=None,
        data_until=None,
        data_duration=DATA_DURATION_NONE,

        query_split=None,
        merge_split=None,

        query_declare={
            'index_identity': ([str], [],                   False,  ''),
            'exchange':       ([str], [],                   False,  ''),
        },
        result_declare={
            'index_identity': (['str'], [],                 True,  ''),
            'code':           (['str'], [],                 True,  ''),
            'name':           (['str'], [],                 True,  ''),
            'fullname':       (['str'], [],                 True,  ''),
            'exchange':       (['str'], [],                 True,  ''),
            'publisher':      (['str'], [],                 True,  ''),
            'listing_date':   (['datetime'], [],            True,  ''),
        },
    )

    DECLARE_DATA_AGENT(
        uri='Market.TradeCalender',
        database='StockAnalysisSystem',
        table_prefix='',

        identity_field='exchange',
        identity_update_list=UPDATE_LIST_EXCHANGE,

        datetime_field='trade_date',
        data_since=TIME_A_SHARE_MARKET_START,
        data_until=TIME_TODAY,
        data_duration=DATA_DURATION_DAILY,

        query_split=None,
        merge_split=None,

        query_declare={
            'index_identity': ([str], [],                   False,  ''),
            'exchange':       ([str], [],                   False,  ''),
        },
        result_declare={
            'index_identity': (['str'], [],                 True,  ''),
            'code':           (['str'], [],                 True,  ''),
            'name':           (['str'], [],                 True,  ''),
            'fullname':       (['str'], [],                 True,  ''),
            'exchange':       (['str'], [],                 True,  ''),
            'publisher':      (['str'], [],                 True,  ''),
            'listing_date':   (['datetime'], [],            True,  ''),
        },
    )
















