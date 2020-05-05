from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.time_utility import *
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.time_utility import *
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


def __default_test_factor(sas: StockAnalysisSystem, factors: [str]):
    if not isinstance(factors, (list, tuple)):
        factors = [factors]
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    df = data_center.query_from_factor('Factor.Finance', '000021.SZSE', (default_since(), now()),
                                       fields=factors, readable=True)
    print(df)
    assert df is not None and len(df) > 0

    for fct in factors:
        assert fct in df.columns


def test_amazing_formula_factor(sas: StockAnalysisSystem):
    __default_test_factor(sas, '资本收益率')


def test_roe(sas: StockAnalysisSystem):
    __default_test_factor(sas, '净资产收益率')


def test_roa(sas: StockAnalysisSystem):
    __default_test_factor(sas, '总资产收益率')


def test_gross_margin(sas: StockAnalysisSystem):
    __default_test_factor(sas, '毛利率')


def test_operating_margin(sas: StockAnalysisSystem):
    __default_test_factor(sas, '营业利润率')


def test_net_profit_rate(sas: StockAnalysisSystem):
    __default_test_factor(sas, '净利润率')


def test_entry(sas: StockAnalysisSystem):
    test_amazing_formula_factor(sas)
    test_roe(sas)
    test_roa(sas)

    test_gross_margin(sas)
    test_operating_margin(sas)
    test_net_profit_rate(sas)





