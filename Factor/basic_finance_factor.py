import pandas as pd
from datetime import date

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Factor.FactorUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
except Exception as e:
    sys.path.append(root_path)

    from Factor.FactorUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
finally:
    pass


def factor_cash_per_loan(identity: str or [str], time_serial: tuple, mapping: dict,
                         data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    fields = ['货币资金', '短期借款', '一年内到期的非流动负债',
              '其他流动负债', '长期借款', '应付债券', '其他非流动负债']
    df = query_finance_pattern(data_hub, identity, time_serial, fields, mapping)

    df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
    df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']

    df['货币资金/有息负债'] = df['货币资金'] / df['有息负债']
    df['货币资金/短期负债'] = df['货币资金'] / df['短期负债']

    return df[['货币资金/有息负债', '货币资金/短期负债'] + ['stock_identity', 'period']]


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
    '67392ca6-f081-41e5-8dde-9530148bf203': (
        ('货币资金/有息负债', '货币资金/短期负债'),
        ('货币资金', '短期借款', '一年内到期的非流动负债', '其他流动负债', '长期借款', '应付债券', '其他非流动负债'),
        '', factor_cash_per_loan, None, None, None),
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
    '83172ea4-5cd2-4bb2-8703-f66fdba9e58b': (),
    'a518ccd5-525e-4d5f-8e84-1f77bbb8f7af': (),
    'f747c9b1-ed98-4a28-8107-d3fa13d0e5ed': (),
    '6c568b09-3aee-4a6a-8440-542dfc5e8dc5': (),
    'f4d0cc16-afa5-4bf4-a7eb-0a44074634ec': (),
    '308e04df-6bc7-4724-bbc5-168232327ac6': (),
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '',
        'plugin_name': 'DummyFactor',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Sleepy'],
        'factor': FACTOR_TABLE,
    }


def plugin_capacities() -> list:
    return list(FACTOR_TABLE.keys())


# ----------------------------------------------------------------------------------------------------------------------

def calculate(factor: str, identity: str or [str], time_serial: tuple, mapping: dict,
              data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    for hash, prob in FACTOR_TABLE.items():
        provides, depends, comments, entry, _, _, _ = prob
        if factor in provides:
            return entry(identity, time_serial, mapping, data_hub, database, extra)
    return None

