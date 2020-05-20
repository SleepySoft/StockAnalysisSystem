import pandas as pd

from StockAnalysisSystem.core.Utiltity.FactorUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


def factor_current_ratio(identity: str or [str], time_serial: tuple, mapping: dict,
                         data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    fields = ['流动资产合计', '流动负债合计']
    df = query_finance_pattern(data_hub, identity, time_serial, fields, mapping)

    df['流动比率'] = df['流动资产合计'] / df['流动负债合计']

    return df[['流动比率'] + ['stock_identity', 'period']]


def factor_quick_ratio(identity: str or [str], time_serial: tuple, mapping: dict,
                         data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    fields = ['流动资产合计', '流动负债合计', '存货', '预付款项', '待摊费用', '长期待摊费用']
    df = query_finance_pattern(data_hub, identity, time_serial, fields, mapping)

    # TODO: The TuShare document updated. We should also update the alias table and re-download data.

    if '待摊费用' in df.columns:
        df['速动比率'] = (df['流动资产合计'] - df['存货'] - df['预付款项'] - df['待摊费用']) / df['流动负债合计']
    else:
        df['速动比率'] = (df['流动资产合计'] - df['存货'] - df['预付款项'] - df['长期待摊费用']) / df['流动负债合计']

    return df[['速动比率'] + ['stock_identity', 'period']]


# ----------------------------------------------------------------------------------------------------------------------

FACTOR_TABLE = {
    '77d075b3-fa36-446b-a31e-855ea5d1fdaa': (
        '流动比率',
        ('流动资产合计', '流动负债合计'),
        '流动比率 = 流动资产合计 / 流动负债合计 * 100%',
        factor_current_ratio, None, None, None
    ),

    '0ac83c45-af48-421e-a7ce-8fc128adf799': (
        '速动比率',
        ('流动资产合计', '流动负债合计', '存货', '预付款项', '待摊费用', '长期待摊费用'),
        '速动比率 = (流动资产合计 - 存货 - 预付款项 - 待摊费用) / 流动负债合计 * 100%',
        factor_quick_ratio, None, None, None
    ),

    # '83172ea4-5cd2-4bb2-8703-f66fdba9e58b': (),
    #
    # 'a518ccd5-525e-4d5f-8e84-1f77bbb8f7af': (),
    # 'f747c9b1-ed98-4a28-8107-d3fa13d0e5ed': (),
    # '6c568b09-3aee-4a6a-8440-542dfc5e8dc5': (),
    # 'f4d0cc16-afa5-4bf4-a7eb-0a44074634ec': (),
    # '308e04df-6bc7-4724-bbc5-168232327ac6': (),
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '',
        'plugin_name': 'Basic Finince Factor',
        'plugin_version': '0.0.0.1',
        'tags': ['Basic', 'Sleepy'],
        'factor': FACTOR_TABLE,
    }


def plugin_capacities() -> list:
    return list(FACTOR_TABLE.keys())


# ----------------------------------------------------------------------------------------------------------------------

def calculate(factor: str, identity: str or [str], time_serial: tuple, mapping: dict,
              data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame or None:
    return dispatch_calculation_pattern(factor, identity, time_serial, mapping, data_hub, database, extra, FACTOR_TABLE)

