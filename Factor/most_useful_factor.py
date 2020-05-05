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


# Tushare has this item
# '[息税前利润] = [息税前利润] + [应付利息];'

engine_amazing_formula = FinanceFactorEngine(
    '[资本收益率] = [息税前利润] / ([净营运资本] + [固定资产]);'
    '[净营运资本] = [应收账款] + [其他应收款] + [预付款项] + [存货] - [无息流动负债] + [长期股权投资] + [投资性房地产];'
    '[无息流动负债] = [应付账款] + [预收款项] + [应付职工薪酬] + [应交税费] + [其他应付款] + [预提费用] + [递延收益] + [其他流动负债];',
    '来自神奇公式网，用以评估公司的收益率')

engine_roe = FinanceFactorEngine(
    '[净资产收益率] = [净利润(含少数股东损益)]  / ([资产总计] - [负债合计]);',
    '即ROE，是衡量企业获利能力的重要指标')

engine_roa = FinanceFactorEngine(
    '[总资产收益率] = [净利润(含少数股东损益)]  / [资产总计];',
    '即ROA，用来衡量每单位资产创造多少净利润的指标，也可以解释为企业利润额与企业平均资产的比率')


# ----------------------------------------------------------------------------------------------------------------------

FACTOR_TABLE = {
    '7ac29c74-3eaf-4c07-92a2-cc95785ff609': (engine_amazing_formula.prob()),
    'be691db4-6017-4671-8fc9-15bd1ea09eb9': (engine_roe.prob()),
    '46334e72-897f-4a45-9c07-b549678eff32': (engine_roa.prob()),
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '',
        'plugin_name': 'Amazing Formula Factor',
        'plugin_version': '0.0.0.1',
        'tags': ['Amazing', 'Sleepy'],
        'factor': FACTOR_TABLE,
    }


def plugin_capacities() -> list:
    return list(FACTOR_TABLE.keys())


# ----------------------------------------------------------------------------------------------------------------------

def calculate(factor: str, identity: str or [str], time_serial: tuple, mapping: dict,
              data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame or None:
    return dispatch_calculation_pattern(factor, identity, time_serial, mapping, data_hub, database, extra, FACTOR_TABLE)

