import pandas as pd

from StockAnalysisSystem.core.Utiltity.FactorUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


def factor_asset_and_loan(identity: str or [str], time_serial: tuple, mapping: dict,
                         data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    fields = ['资产总计', '货币资金', '交易性金融资产', '可供出售金融资产',
              '短期借款', '一年内到期的非流动负债', '其他流动负债', '长期借款', '应付债券', '其他非流动负债']
    df = query_finance_pattern(data_hub, identity, time_serial, fields, mapping)

    df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
    df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']
    df['金融资产'] = df['交易性金融资产'] + df['可供出售金融资产']

    df['货币资金/有息负债'] = df['货币资金'] / df['有息负债']
    df['货币资金/短期负债'] = df['货币资金'] / df['短期负债']
    df['有息负债/资产总计'] = df['有息负债'] / df['资产总计']
    df['有息负债/货币金融资产'] = df['有息负债'] / (df['货币资金'] + df['金融资产'])

    return df[['货币资金/有息负债', '货币资金/短期负债', '有息负债/资产总计', '有息负债/货币金融资产'] +
              ['stock_identity', 'period']]


# ----------------------------------------------------------------------------------------------------------------------

FACTOR_TABLE = {
    '67392ca6-f081-41e5-8dde-9530148bf203': (
        ('货币资金/有息负债', '货币资金/短期负债', '有息负债/资产总计', '有息负债/货币金融资产'),
        ('资产总计', '货币资金', '交易性金融资产', '可供出售金融资产',
         '短期借款', '一年内到期的非流动负债', '其他流动负债', '长期借款', '应付债券', '其他非流动负债'),
        '老唐的指标，其中 短期负债 = 短期借款 + 一年内到期的非流动负债 + 其他流动负债；有息负债 = 短期负债 + 长期借款 + 应付债券 + 其他非流动负债',
        factor_asset_and_loan, None, None, None),
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '',
        'plugin_name': 'Tang Finance Factor',
        'plugin_version': '0.0.0.1',
        'tags': ['Tang', 'Sleepy'],
        'factor': FACTOR_TABLE,
    }


def plugin_capacities() -> list:
    return list(FACTOR_TABLE.keys())


# ----------------------------------------------------------------------------------------------------------------------

def calculate(factor: str, identity: str or [str], time_serial: tuple, mapping: dict,
              data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame or None:
    return dispatch_calculation_pattern(factor, identity, time_serial, mapping, data_hub, database, extra, FACTOR_TABLE)

