import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext


once: bool = True
subServiceContext: SubServiceContext = None
SERVICE_ID = 'f38cbc96-3b94-4cf2-bb36-fd9d4e656025'


# ----------------------------------------------------------------------------------------------------------------------

def test_entry():
    df = subServiceContext.sas_api.data_center().query('Result.Analyzer', '000004.SZSE')
    df = df.sort_values(by="analyzer").drop_duplicates(subset=["period"], keep="last")

    print(df)


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
        test_entry()
        once = False

