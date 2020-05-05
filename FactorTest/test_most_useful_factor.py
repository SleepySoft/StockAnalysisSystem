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


def test_amazing_formula_factor(sas: StockAnalysisSystem):
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    df = data_center.query_from_factor('Factor.Finance', '000021.SZSE', (default_since(), now()),
                                       fields=['资本收益率'], readable=True)
    print(df)
    assert df is not None and len(df) > 0
    assert '资本收益率' in df.columns


def test_roe(sas: StockAnalysisSystem):
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    df = data_center.query_from_factor('Factor.Finance', '000021.SZSE', (default_since(), now()),
                                       fields=['净资产收益率'], readable=True)
    print(df)
    assert df is not None and len(df) > 0
    assert '净资产收益率' in df.columns


def test_roa(sas: StockAnalysisSystem):
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    df = data_center.query_from_factor('Factor.Finance', '000021.SZSE', (default_since(), now()),
                                       fields=['总资产收益率'], readable=True)
    print(df)
    assert df is not None and len(df) > 0
    assert '总资产收益率' in df.columns


def test_entry(sas: StockAnalysisSystem):
    test_amazing_formula_factor(sas)
    test_roe(sas)
    test_roa(sas)





