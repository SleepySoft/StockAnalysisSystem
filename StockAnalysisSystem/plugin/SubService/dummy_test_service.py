import traceback

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.Utility.digit_utility import to_int
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext


once: bool = True
subServiceContext: SubServiceContext = None
SERVICE_ID = 'f38cbc96-3b94-4cf2-bb36-fd9d4e656025'


# ----------------------------------------------------------------------------------------------------------------------

def test_entry():
    stock_identity = '000004.SZSE'

    df = subServiceContext.sas_api.data_center().query('Result.Analyzer', '000004.SZSE')
    if df is None or df.empty:
        return
    df = df.sort_values(by="period").drop_duplicates(subset=["analyzer"], keep="last")

    print(df)

    stock_name = subServiceContext.sas_api.data_utility().stock_identity_to_name('000004.SZSE')
    text = '%s [%s]' % (stock_name, stock_identity)

    if df.empty:
        return text + '无分析数据'

    strategy_name_dict = subServiceContext.sas_api.strategy_entry().strategy_name_dict()

    text_items = []
    for analyzer, period, brief, score in \
            zip(df['analyzer'], df['period'], df['brief'], df['score']):
        if score is not None and to_int(score, 999) <= 60:
            text_items.append('> %s: %s' % (strategy_name_dict.get(analyzer), brief))

    if len(text_items) == 0:
        text += '未发现风险项目'
    else:
        text += '风险项目\n----------------------------\n'
        text += '\n'.join(text_items)

    print(text)


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'TestEntry',
        'plugin_version': '0.0.0.1',
        'tags': ['Test', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return [
        'polling',        # polling() function will be invoked while event processing thread is free
    ]


# ----------------------------------------------------------------------------------------------------------------------

def init(sub_service_context: SubServiceContext) -> bool:
    try:
        global subServiceContext
        subServiceContext = sub_service_context
    except Exception as e:
        import traceback
        print('Plugin-in init error: ' + str(e))
        print(traceback.format_exc())
    finally:
        pass
    return True


def startup() -> bool:
    return True


def polling(interval_ns: int):
    global once
    if once:
        try:
            test_entry()
        except Exception as e:
            print("Test exception")
            print(e)
            print(traceback.format_exc())
        finally:
            once = False

