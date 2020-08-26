from .DataAgent import *
from ..UniversalDataDepot.DepotMongoDB import *
from ..Database.DatabaseEntry import DatabaseEntry


def uri_to_table(uri: str) -> str:
    return uri.replace('.', '_')


def build_data_agent(database_entry: DatabaseEntry):
    mongodb_client = database_entry.get_mongo_db_client()

    return [
        # -------------------------- Market Data --------------------------

        DataAgent(
            uri='Market.SecuritiesInfo',
            depot=DepotMongoDB(primary_keys='stock_identity',
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Market.SecuritiesInfo')),
            identity_field='stock_identity',
            datetime_field=None,
            data_duration=DATA_DURATION_NONE,
        ),

        DataAgent(
            uri='Market.IndexInfo',
            depot=DepotMongoDB(primary_keys='index_identity',
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Market.IndexInfo')),
            identity_field='index_identity',
            datetime_field=None,
            data_duration=DATA_DURATION_NONE,
        ),

        DataAgent(
            uri='Market.TradeCalender',
            depot=DepotMongoDB(primary_keys=['exchange', 'trade_date'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Market.TradeCalender')),
            identity_field='exchange',
            datetime_field='trade_date',
            data_duration=DATA_DURATION_DAILY,
            update_list=DataAgentUtility.support_exchange_list,
        ),

        DataAgent(
            uri='Market.Enquiries',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'enquiry_date'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Market.Enquiries')),
            identity_field='stock_identity',
            datetime_field='enquiry_date',
            data_duration=DATA_DURATION_FLOW,
        ),

        # No this data anymore
        # DataAgent(
        #     uri='Market.Investigation',
        #     depot=DepotMongoDB(primary_keys=['stock_identity', 'investigate_date'],
        #                        client=mongodb_client,
        #                        database='StockAnalysisSystem',
        #                        data_table=uri_to_table('Market.Investigation')),
        #     identity_field='stock_identity',
        #     datetime_field='investigate_date',
        #     data_duration=DATA_DURATION_FLOW,
        # ),

        DataAgent(
            uri='Market.NamingHistory',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'naming_date'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Market.NamingHistory')),
            identity_field='stock_identity',
            datetime_field='naming_date',
            data_duration=DATA_DURATION_FLOW,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Market.SecuritiesTags',
            depot=DepotMongoDB(primary_keys='stock_identity',
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Market.SecuritiesTags')),
            identity_field='stock_identity',
            datetime_field=None,
            data_duration=DATA_DURATION_NONE,
            update_list=DataAgentUtility.a_stock_list,
        ),

        # -------------------------- Finance Data --------------------------

        DataAgent(
            uri='Finance.Audit',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Finance.Audit')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Finance.BalanceSheet',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Finance.BalanceSheet')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Finance.IncomeStatement',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Finance.IncomeStatement')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Finance.CashFlowStatement',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Finance.CashFlowStatement')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Finance.BusinessComposition',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Finance.BusinessComposition')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
            update_list=DataAgentUtility.a_stock_list,
        ),

        # ----------------------- Stockholder & Pledge -----------------------

        DataAgent(
            uri='Stockholder.Statistics',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Stockholder.Statistics')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Stockholder.PledgeStatus',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'due_date'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Stockholder.PledgeStatus')),
            identity_field='stock_identity',
            datetime_field='due_date',
            data_duration=DATA_DURATION_FLOW,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='Stockholder.PledgeHistory',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'due_date'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Stockholder.PledgeHistory')),
            identity_field='stock_identity',
            datetime_field='due_date',
            data_duration=DATA_DURATION_FLOW,
            update_list=DataAgentUtility.a_stock_list,
        ),

        # ----------------------- Trade Data - Daily -----------------------

        DataAgent(
            uri='TradeData.Stock.Daily',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'trade_date'],
                               client=mongodb_client,
                               database='StockDaily',
                               data_table=uri_to_table('TradeData.Stock.Daily')),
            identity_field='stock_identity',
            datetime_field='trade_date',
            data_duration=DATA_DURATION_DAILY,
            update_list=DataAgentUtility.a_stock_list,
        ),

        DataAgent(
            uri='TradeData.Index.Daily',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'trade_date'],
                               client=mongodb_client,
                               database='StockDaily',
                               data_table=uri_to_table('TradeData.Index.Daily')),
            identity_field='stock_identity',
            datetime_field='trade_date',
            data_duration=DATA_DURATION_DAILY,
            update_list=DataAgentUtility.support_index_list,
        ),

        # -------------------- Metrics and Factor - Daily --------------------

        DataAgent(
            uri='Metrics.Stock.Daily',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'trade_date'],
                               client=mongodb_client,
                               database='StockDaily',
                               data_table=uri_to_table('Metrics.Stock.Daily')),
            identity_field='stock_identity',
            datetime_field='trade_date',
            data_duration=DATA_DURATION_DAILY,
            update_list=DataAgentUtility.a_stock_list,
        ),

        # ------------------------ Factor - Quarter ------------------------

        DataAgent(
            uri='Factor.Finance',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                               client=mongodb_client,
                               database='StockAnalysisSystem',
                               data_table=uri_to_table('Factor.Finance')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
        ),

        # --------------------- Result Cache - Quarter ---------------------

        DataAgent(
            uri='Result.Analyzer',
            depot=DepotMongoDB(primary_keys=['stock_identity', 'period', 'analyzer'],
                               client=mongodb_client,
                               database='SasCache',
                               data_table=uri_to_table('Result.Analyzer')),
            identity_field='stock_identity',
            datetime_field='period',
            data_duration=DATA_DURATION_QUARTER,
        ),
    ]




















