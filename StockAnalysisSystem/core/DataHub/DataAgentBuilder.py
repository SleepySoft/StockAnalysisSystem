from .DataAgent import *
from ..Database.DatabaseEntry import DatabaseEntry


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

            identity_field='index_identity',
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

        DataAgentExchangeData(
            uri='Market.TradeCalender',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='exchange',
            datetime_field='trade_date',

            query_declare={
                'exchange':     ([str], ['SSE', 'SZSE', 'A-SHARE'], True,  ''),
                'trade_date':   ([tuple], [],                       False,  ''),
            },
            result_declare={
                 'exchange':   (['str'], ['SSE', 'SZSE'],           True,  ''),
                 'trade_date': (['datetime'], [],                   True,  ''),
                 'status':     (['int'], [],                        True,  ''),
            },

            data_duration=DATA_DURATION_DAILY,
        ),

        DataAgent(
            uri='Market.Enquiries',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='enquiry_date',

            query_declare={
                'stock_identity': ([str], [],                   False,  ''),
                'exchange':       ([str], [],                   False,  ''),
                'enquiry_date':   ([tuple, datetime, None], [], False,  ''),
            },
            result_declare={
                'stock_identity': (['str'], [],                 True,  ''),
                'exchange':       (['str'], [],                 True,  ''),
                'enquiry_date':   (['datetime'], [],            True,  ''),
                'enquiry_topic':   (['str'], [],                True,  ''),
                'enquiry_title':   (['str'], [],                False,  ''),
            },

            data_duration=DATA_DURATION_FLOW,
        ),

        DataAgent(
            uri='Market.Investigation',
            database_entry=database_entry,

            depot_name='StockAnalysisSystem',
            table_prefix='',

            identity_field='stock_identity',
            datetime_field='investigate_date',

            query_declare={
                'stock_identity':    ([str], [],                   False,  ''),
                'investigate_date':  ([tuple, datetime, None], [], False,  ''),
            },
            result_declare={
                'stock_identity':    (['str'], [],                 True,  ''),
                'investigate_date':  (['datetime'], [],            True,  ''),
                'investigate_topic': (['str'], [],                 False, ''),
                'investigate_reason': (['str'], [],                True,  ''),
            },

            data_duration=DATA_DURATION_FLOW,
        ),

        DataAgentStockData(
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

        DataAgentStockData(
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
                'agency':         (['str'], [],         True, '会计事务所'),
                'sign':           (['str'], [],         True, '签字会计师'),
            },
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

        DataAgentStockData(
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

        DataAgentStockData(
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

        DataAgentIndexDaily(
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




















