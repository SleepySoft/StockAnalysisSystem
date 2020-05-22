import pandas as pd

from StockAnalysisSystem.core.Utiltity.FactorUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


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


engine_gross_margin = FinanceFactorEngine(
    '[毛利率] = ([营业收入] - [减:营业成本])  / [营业收入];',
    '毛利占销售收入的百分比，是一个衡量盈利能力的指标')

engine_operating_margin = FinanceFactorEngine(
    '[营业利润率] = [营业利润] / [营业收入];',
    '企业的营业利润与营业收入的比率。它是衡量企业经营效率的指标，反映了在不考虑非营业成本的情况下，企业管理者通过经营获取利润的能力')

engine_net_profit_rate = FinanceFactorEngine(
    '[净利润率] = [净利润(含少数股东损益)] / ([营业收入] - [其他业务收入]);',
    '扣除所有成本、费用和企业所得税后的利润率。是反映公司盈利能力的一项重要指标')


# ----------------------------------------------------------------------------------------------------------------------

FACTOR_TABLE = {
    '7ac29c74-3eaf-4c07-92a2-cc95785ff609': (engine_amazing_formula.prob()),
    'be691db4-6017-4671-8fc9-15bd1ea09eb9': (engine_roe.prob()),
    'af9d5054-94d1-446f-908d-f8b69e749c86': (engine_roa.prob()),
    '17310941-2a46-409c-9d7e-a90a0c45ccd2': (engine_gross_margin.prob()),
    '8bd33345-0580-474f-8979-f7635ce96c0d': (engine_operating_margin.prob()),
    '258bc63e-c726-480b-8fa8-05db460f11dd': (engine_net_profit_rate.prob()),
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

