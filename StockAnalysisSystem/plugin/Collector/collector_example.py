import pandas as pd
from zs import data_get as dg, data_config as dc


def plugin_prob() -> dict:
    return {
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['example', 'collector']
    }


def plugin_adapt(uri: str) -> bool:
    return True


def plugin_capacities() -> list:  # 数据名字添加
    return [dc.repurchase, dc.share_float]


def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == dc.repurchase:
        return dg.TsData().repurchase_get_data()
    elif uri == dc.share_float:
        return dg.TsData().share_float_get_data()
    else:
        return None


def validate(**kwargs) -> bool:
    pass
    return True


def fields() -> dict:
    return {}


# def query(**kwargs) -> pd.DataFrame or None:
#     uri = kwargs.get('uri')
#     if uri == flog:
#         return pd.DataFrame({
#             'ibd': ['300783.SZ', '1StockA', '2StockB', 'StockB', 'StockC', 'StockC'],
#             'time2': [datetime(1995, 1, 1), datetime(1996, 1, 1),    # StockA
#                       datetime(2002, 2, 1), datetime(2005, 5, 1),    # StockB
#                       datetime(2020, 3, 1), datetime(2021, 1, 1)],   # StockC
#             'field11': [100., 20., 30., 40., 500., 600.],
#             'field22': ['A', 'B', 'C', 'D', 'E', 'F'],
#         })
#     else:
#         return None
















































