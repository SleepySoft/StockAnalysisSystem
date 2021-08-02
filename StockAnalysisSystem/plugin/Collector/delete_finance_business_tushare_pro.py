import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.CollectorUtility import *


# ----------------------------------------------------------------------------------------------------------------------

FIELDS = {
    'Finance.BusinessComposition': {
        'bz_item': '主营业务来源',
        'bz_sales': '主营业务收入(元)',
        'bz_profit': '主营业务利润(元)',
        'bz_cost': '主营业务成本(元)',
        'curr_type': '货币代码',
        'update_flag': '是否更新',
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

# fina_mainbz: https://tushare.pro/document/2?doc_id=81

def __fetch_bussiness_data_by_type(pro: ts.pro_api, ts_code: str, classify: str,
                                   since: datetime.datetime, until: datetime.datetime):
    limit = 10
    result = None
    derive_time = until
    while limit > 0:
        ts_since = since.strftime('%Y%m%d')
        ts_until = derive_time.strftime('%Y%m%d')

        ts_delay('fina_mainbz')
        sub_result = pro.fina_mainbz(ts_code=ts_code, start_date=ts_since, end_date=ts_until, type=classify)
        if not isinstance(sub_result, pd.DataFrame) or sub_result.empty:
            break
        result = pd.concat([result, sub_result])
        result = result.reset_index(drop=True)

        result_since = min(sub_result['end_date'])
        result_since = text_auto_time(result_since)

        # End condition
        if result_since == derive_time or len(sub_result) < 100:
            break
        limit -= 1
        derive_time = result_since
    if isinstance(result, pd.DataFrame):
        result = result.drop_duplicates()

    return result


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

        try:
            if is_slice_update(ts_code, since, until):
                ts_since = since.strftime('%Y%m%d')

                clock = Clock()
                result_product = pro.fina_mainbz_vip(ts_since, type='P')
                result_area = pro.fina_mainbz_vip(ts_since, type='D')
                print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))
            else:
                clock = Clock()
                result_product = __fetch_bussiness_data_by_type(pro, ts_code, 'P', since, until)
                result_area = __fetch_bussiness_data_by_type(pro, ts_code, 'D', since, until)
                print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            if isinstance(result_product, pd.DataFrame) and not result_product.empty:
                result_product['classification'] = 'product'
            if isinstance(result_area, pd.DataFrame) and not result_area.empty:
                result_area['classification'] = 'area'
            result = pd.merge(result_product, result_area, on=['ts_code', 'end_date'])

            # for year in range(since_year, until_year):
            #     ts_date = '%02d1231' % year
            #     # 抱歉，您每分钟最多访问该接口60次
            #     ts_delay('fina_mainbz')
            #     sub_result = pro.fina_mainbz(ts_code=ts_code, start_date=ts_date, end_date=ts_date)
            #     result = pd.concat([result, sub_result])
            # print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            # result.fillna(0.0)
            # del result['ts_code']
            # result.reset_index()
            # business = result.groupby('end_date').apply(
            #     lambda x: x.drop('end_date', axis=1).to_dict('records'))
            # result = pd.DataFrame.from_dict({'business': business}, orient='index').reset_index()
            # result['ts_code'] = ts_code
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        finally:
            pass

    check_execute_dump_flag(result, **kwargs)

    if isinstance(result, pd.DataFrame) and not result.empty:
        result.fillna('', inplace=True)
        convert_ts_code_field(result)
        convert_ts_date_field(result, 'end_date')
    # if result is not None:
    #     result['period'] = pd.to_datetime(result['end_date'])
    #     result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)

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

