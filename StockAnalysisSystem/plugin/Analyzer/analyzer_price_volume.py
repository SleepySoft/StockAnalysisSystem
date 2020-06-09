import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


METHOD_LIST = [
    ('c9377cd7-f646-4e90-b1e2-544897c854d5', '',        '',                   None),
    ('6192183b-23f9-42be-83a2-0fe4bf86b75e', '',        '',                   None),
    ('c5d443c0-f309-483c-bca8-29033bd3acf1', '',        '',                   None),
    ('88817184-3123-4148-9596-af0f097a6202', '',        '',                   None),
    ('7fa664a6-e965-4dad-bb26-11b17a484253', '',        '',                   None),
    ('0208ee88-612a-42b3-866f-f01055fc05d7', '',        '',                   None),
]


# def plugin_prob() -> dict:
#     return {
#         'plugin_id': 'bf418062-7f2e-4125-9dbb-e6fd09e079e2',
#         'plugin_name': 'analyzer_price_volume',
#         'plugin_version': '0.0.0.1',
#         'tags': ['price_volume', 'analyzer'],
#         'methods': METHOD_LIST,
#     }
#
#
# def plugin_adapt(method: str) -> bool:
#     return method in methods_from_prob(plugin_prob())


def plugin_capacities() -> list:
    return [
        'score',
    ]


# ----------------------------------------------------------------------------------------------------------------------

def analysis(methods: [str], securities: [str], time_serial: tuple,
             data_hub: DataHubEntry, database: DatabaseEntry, **kwargs) -> [AnalysisResult]:
    return standard_dispatch_analysis(methods, securities, time_serial, data_hub, database, kwargs, METHOD_LIST)
















