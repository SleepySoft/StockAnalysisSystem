import logging
from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from DataHub.DataAgent import *
    from Database.DatabaseEntry import DatabaseEntry
except Exception as e:
    sys.path.append(root_path)
    from DataHub.DataAgent import *
    from Database.DatabaseEntry import DatabaseEntry
finally:
    logger = logging.getLogger('')


def build_data_agent(database_entry: DatabaseEntry):
    PARAMETER_FINANCE_DATA = {
        'database_entry': database_entry,

        'depot_name': 'StockAnalysisSystem',
        'table_prefix': '',

        'identity_field': 'stock_identity',
        'datetime_field': 'period',

        'query_declare': {
            'stock_identity': ([str], [], False, ''),
            'period': ([tuple, None], [], False, ''),
        },
        'result_declare': {
            'stock_identity': (['str'], [], True, ''),
            'period': (['datetime'], [], True, ''),
        },

        'data_duration': DATA_DURATION_QUARTER,
    }

    return [
        DataAgent(
            uri='Market.SecuritiesInfo',
            database_entry=database_entry,

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

        DataAgent(
            uri='Market.IndexInfo',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field=None,

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

            data_duration=DATA_DURATION_NONE,
        ),

        DataAgent(
            uri='Market.TradeCalender',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='exchange',
            datetime_field='trade_date',

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

            data_duration=DATA_DURATION_DAILY,
        ),

        DataAgent(
            uri='Market.NamingHistory',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='naming_date',

            query_declare={
                'stock_identity': ([str], [],                   False,  ''),
                'naming_date':    ([tuple, datetime, None], [], False,  ''),
            },
            result_declare={
                'stock_identity': (['str'], [],                 True,  ''),
                'name':           (['str'], [],                 True,  ''),
                'naming_date':    (['datetime'], [],            True,  ''),
            },

            data_duration=DATA_DURATION_FLOW,
        ),

        DataAgent(
            uri='Market.SecuritiesTags',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field=None,

            query_declare={
                'stock_identity': ([str], [],           False, ''),
            },
            result_declare={
                'stock_identity': (['str'], [],         True, ''),
            },

            data_duration=DATA_DURATION_NONE,
        ),

        DataAgentStockQuarter(
            uri='Finance.Audit',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='period',

            query_declare={
                'stock_identity': ([str], [],                           False, ''),
                'period':         ([tuple,  None], [],                  False, ''),
            },
            result_declare={
                'stock_identity': (['str'], [],         True, ''),
                'period':         (['datetime'], [],    True, ''),                  # The last day of report period
                'conclusion':     (['str'], [],         True, '审计结果'),
                'agency': (['str'], [],                 True, '会计事务所'),
                'sign': (['str'], [],                   True, '签字会计师'),
            },

            data_duration=DATA_DURATION_QUARTER,
        ),

        DataAgentStockQuarter(
            uri='Finance.BalanceSheet',
            **PARAMETER_FINANCE_DATA
        ),

        DataAgentStockQuarter(
            uri='Finance.IncomeStatement',
            **PARAMETER_FINANCE_DATA
        ),

        DataAgentStockQuarter(
            uri='Finance.CashFlowStatement',
            **PARAMETER_FINANCE_DATA
        ),

        DataAgentStockQuarter(
            uri='Finance.BusinessComposition',
            **PARAMETER_FINANCE_DATA
        ),

        DataAgentStockQuarter(
            uri='Stockholder.Statistics',
            **PARAMETER_FINANCE_DATA
        ),

        DataAgent(
            uri='Stockholder.PledgeStatus',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='due_date',

            query_declare={
                'stock_identity': ([str], [],                           False, ''),
                'due_date':       ([tuple,  None], [],                  False, ''),
            },
            result_declare={
                'stock_identity': (['str'], [],         True, ''),
                'due_date':       (['datetime'], [],    True, ''),
                'pledge_count':   (['int'], [],         True, ''),
                'pledge_ratio':   (['float'], [],       True, ''),
            },

            data_duration=DATA_DURATION_FLOW,
        ),

        DataAgent(
            uri='Stockholder.PledgeHistory',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='due_date',

            query_declare={
                'stock_identity': ([str], [],                           False, ''),
                'due_date':       ([tuple,  None], [],                  False, ''),
            },
            result_declare={
                # TODO: TBD
                'stock_identity': (['str'], [],         True, ''),
                'due_date':       (['datetime'], [],    True, ''),
            },

            data_duration=DATA_DURATION_FLOW,
        ),

        DataAgentSecurityDaily(
            uri='TradeData.Stock.Daily',
            database_entry=database_entry,

            depot_name='StockDaily',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='trade_date',

            query_declare={
                'stock_identity': ([str], [],           True,  ''),
                'trade_date':     ([tuple, None], [],   False, ''),
            },
            result_declare={
                'trade_date':     (['datetime'], [],    True, ''),
            },
        ),

        DataAgentSecurityDaily(
            uri='TradeData.Index.Daily',
            database_entry=database_entry,

            depot_name='StockDaily',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='trade_date',

            query_declare={
                'stock_identity': ([str], [],           True,  ''),
                'trade_date':     ([tuple, None], [],   False, ''),
            },
            result_declare={
                'trade_date':     (['datetime'], [],    True, ''),
            },
        ),

        DataAgentFactorQuarter(
            uri='Factor.Finance',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='trade_date',

            query_declare={
                'stock_identity': ([str], [],           True,  ''),
                'trade_date':     ([tuple, None], [],   False, ''),
            },
            result_declare={
                'trade_date':     (['datetime'], [],    True, ''),
            },
        ),
    ]




















