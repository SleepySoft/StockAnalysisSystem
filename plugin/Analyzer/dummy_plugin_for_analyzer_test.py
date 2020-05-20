import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


# ----------------------------------------------------------------------------------------------------------------------

def score_1(securities: str, data_hub: DataHubEntry,
            database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)
    nop(database)
    nop(context)
    end_char = securities.split('.')[0][-1:]
    score = int(end_char) * 10
    return AnalysisResult(securities, score, end_char + ' * 10 = ' + str(score))


def score_2(securities: str, data_hub: DataHubEntry,
            database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)
    nop(database)
    nop(context)
    end_char = securities.split('.')[0][-1:]
    score = (10 - int(end_char)) * 10
    return AnalysisResult(securities, score, '(10 - ' + end_char + ') * 10 = ' + str(score))


def include_1(securities: str, data_hub: DataHubEntry,
              database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)
    nop(database)
    nop(context)
    end_char = securities.split('.')[0][-1:]
    passed = end_char in ['1', '2', '3', '4', '5']
    return AnalysisResult(securities, passed, '代码末位为' + end_char + '通过测试' if passed else '未通过测试')


def include_2(securities: str, data_hub: DataHubEntry,
              database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)
    nop(database)
    nop(context)
    end_char = securities.split('.')[0][-1:]
    passed = end_char in ['5', '6', '7', '8', '9']
    return AnalysisResult(securities, passed, '代码末位为' + end_char + '通过测试' if passed else '未通过测试')


def exclude_1(securities: str, data_hub: DataHubEntry,
              database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)
    nop(database)
    nop(context)
    passed = securities[0] not in ['1', '2', '3', '4', '5']
    return AnalysisResult(securities, passed, '代码第一位为' + securities[0] + '通过测试' if passed else '未通过测试')


def exclude_2(securities: str, data_hub: DataHubEntry,
              database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)
    nop(database)
    nop(context)
    passed = securities[0] not in ['5', '6', '7', '8', '9']
    return AnalysisResult(securities, passed, '代码第一位为' + securities[0] + '通过测试' if passed else '未通过测试')


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    ('5d19927a-2ab1-11ea-aee4-eb8a702e7495', '评分测试1', '传入的代码末位是几，就打N*10分',       score_1),
    ('bc74b6fa-2ab1-11ea-8b94-03e35eea3ca4', '评分测试2', '传入的代码末位是几，就打10-N*10分',    score_2),
    ('6b23435c-2ab1-11ea-99a8-3f957097f4c9', '包含测试1', '只有代码末位是1-5的能通过此测试',      include_1),
    ('d0b619ba-2ab1-11ea-ac32-43e650aafd4f', '包含测试2', '只有代码末位是5-9的能通过此测试',      include_2),
    ('78ffae34-2ab1-11ea-88ff-634c407b44d3', '排除测试1', '只有代码第一位是1-5的会被排除',        exclude_1),
    ('d905cdea-2ab1-11ea-9e79-ff65d4808d88', '排除测试2', '只有代码第一位是5-9的会被排除',        exclude_2),
]


def plugin_prob() -> dict:
    return {
        'plugin_id': '2806f676-2aad-11ea-8c57-87a2a5d9cf76',
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['test', 'dummy', 'analyzer'],
        'methods': METHOD_LIST,
    }


def plugin_adapt(method: str) -> bool:
    return method in methods_from_prob(plugin_prob())


def plugin_capacities() -> list:
    return [
        'score',
        'inclusive',
        'exclusive',
    ]


# ----------------------------------------------------------------------------------------------------------------------

def analysis(securities: [str], methods: [str], data_hub: DataHubEntry,
             database: DatabaseEntry, extra: dict) -> [AnalysisResult]:
    return standard_dispatch_analysis(securities, methods, data_hub, database, extra, METHOD_LIST)




