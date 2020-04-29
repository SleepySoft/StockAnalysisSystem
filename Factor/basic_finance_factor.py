import pandas as pd
from datetime import date

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
except Exception as e:
    sys.path.append(root_path)

    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
finally:
    pass


def factor_cash_per_loan(df: pd.DataFrame, extra: dict) -> pd.DataFrame:
    df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
    df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']

    df['货币资金/有息负债'] = df['货币资金'] / df['有息负债']
    df['货币资金/短期负债'] = df['货币资金'] / df['短期负债']

    return df


FACTOR_TABLE = {
    '67392ca6-f081-41e5-8dde-9530148bf203': (
        ('货币资金/有息负债', '货币资金/短期负债'),
        ('货币资金', '短期借款', '一年内到期的非流动负债', '其他流动负债', '长期借款', '应付债券', '其他非流动负债'),
        '', factor_cash_per_loan, None, None, None),
    '77d075b3-fa36-446b-a31e-855ea5d1fdaa': (),
    '0ac83c45-af48-421e-a7ce-8fc128adf799': (),
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


# ----------------------------------------------------------------------------------------------------------------------

def calculate(identity: str or [str], factor: [str], time_serial: tuple,
              data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    return None

