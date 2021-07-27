import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.CollectorUtility import *


# ----------------------------------------------------------------------------------------------------------------------

FIELDS = {
    'Finance.BusinessComposition': {
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'finance_business_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

# https://tushare.pro/document/2?doc_id=81

def __fetch_business_data(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        # since_limit = years_ago_of(until, 3)
        # since = max([since, since_limit])

        # Because of the implementation of this interface, we only fetch the annual report
        # since_year = since.year
        # until_year = until.year

        result = None
        pro = ts.pro_api(TS_TOKEN)

        if is_slice_update(ts_code, since, until):
            ts_since = since.strftime('%Y%m%d')
            result = pro.fina_mainbz_vip(ts_since)
        else:
            try:git status
            
                clock = Clock()
                time_iter = DateTimeIterator(since, until)

                while not time_iter.end():
                    quarter = time_iter.iter_quarter_tail()[0]
                    if quarter > now():
                        break
                    ts_date = since.strftime('%Y%m%d')

                    ts_delay('fina_mainbz')
                    sub_result = pro.fina_mainbz(ts_code=ts_code, start_date=ts_date, end_date=ts_date)
                    result = pd.concat([result, sub_result])
                print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

                # for year in range(since_year, until_year):
                #     ts_date = '%02d1231' % year
                #     # 抱歉，您每分钟最多访问该接口60次
                #     ts_delay('fina_mainbz')
                #     sub_result = pro.fina_mainbz(ts_code=ts_code, start_date=ts_date, end_date=ts_date)
                #     result = pd.concat([result, sub_result])
                # print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

                if result is not None and len(result) > 0:
                    result.fillna(0.0)
                    del result['ts_code']
                    result.reset_index()
                    business = result.groupby('end_date').apply(
                        lambda x: x.drop('end_date', axis=1).to_dict('records'))
                    result = pd.DataFrame.from_dict({'business': business}, orient='index').reset_index()
                    result['ts_code'] = ts_code
            except Exception as e:
                print(e)
                print(traceback.format_exc())
            finally:
                pass

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.fillna('')
        result['period'] = pd.to_datetime(result['end_date'])
        result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_business_data(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS

