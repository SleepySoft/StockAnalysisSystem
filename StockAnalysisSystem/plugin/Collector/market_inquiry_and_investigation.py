import pandas as pd
import execjs
import requests_html

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


# ----------------------------------------------------------------------------------------------------------------------

def run_js(js_text: str, invoke: str):
    js_env = execjs.get().name
    print('-----------------------------------------------------------------')
    print('Run java script: ')
    print('Js environment: ' + js_env)
    if js_env == 'JScript':
        print('Warning: Run JS in Windows environment may cause access denied and Security Warning.\n'
              'It is recommended to use NodeJs.')
    else:
        pass
    try:
        context = execjs.compile(js_text)
        return context.call(invoke)
    except Exception as e:
        print('Error: Run JS fail, please check the JS environment and your Security Setting.')
        print(e)
        print(traceback.format_exc())
        return None
    finally:
        print('-----------------------------------------------------------------')


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- Code From LeeXuanhe ------------------------------------------------
# --------------------------------------------- https://gitee.com/leexuanhe --------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

pd.set_option('mode.chained_assignment', None)


##### ##### ##### #####
# http://www.szse.cn/disclosure/supervision/inquire/index.html
# 深交所问询函件
# 全部函件类别 非许可类重组问询函 问询函 许可类重组问询函 第三季报审查问询函 年报问询函 半年报问询函 关注函 公司部函
# 深交所问询函件总页数，需重点关注的为年报问询函
def get_szse_page_num() -> pd.DataFrame:
    ss = requests_html.HTMLSession()
    url = f'http://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=main_wxhj&PAGENO=1'
    res = ss.get(url)
    return res.json()[0]['metadata']['pagecount']


# 深交所问询函件总条数
def get_szse_record_count() -> pd.DataFrame:
    ss = requests_html.HTMLSession()
    url = f'http://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=main_wxhj&PAGENO=1'
    res = ss.get(url)
    return res.json()[0]['metadata']['recordcount']


# 获取单页数据
def get_szse_one_page(page_num: str) -> pd.DataFrame:
    ss = requests_html.HTMLSession()
    url = f'http://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=main_wxhj&PAGENO={page_num}'
    res = ss.get(url)
    try:
        df = pd.DataFrame(res.json()[0]['data'])
        df['ck'] = df['ck'].apply(lambda x: clean_str(x))
        df['hfck'] = df['hfck'].apply(lambda x: clean_str(x))
        return df
    except Exception as e:
        print('Get enquiries from szse fail.')
        print(e)
    finally:
        pass
    return None


# 获取所有数据
def get_szse_all() -> pd.DataFrame:
    pg_num = int(get_szse_page_num()) + 1
    df = pd.DataFrame()
    for _pg in range(1, pg_num):
        loop_df = get_szse_one_page(_pg)
        df = pd.concat([df, loop_df])
    df = df.reset_index(drop=True)
    return df

##### ##### ##### #####
# http://www.sse.com.cn/disclosure/credibility/supervision/inquiries/
# 首页 披露 监管信息公开 公司监管 监管问询
# 获取上交所单页数据
# 上交所数据分为 问询函 定期报告事后审核意见函 重大资产重组预案审核意见函
# 上交所可以支持把单页设置比较大来一次获取所有数据，比如2000


def get_sse_one_page(page_num: str = 1, page_size: str = 15) -> pd.DataFrame:
    ss = requests_html.HTMLSession()
    ss.headers['Referer'] = 'http://www.sse.com.cn/disclosure/credibility/supervision/inquiries/'
    url = f'http://query.sse.com.cn/commonSoaQuery.do?siteId=28&sqlId=BS_KCB_GGLL&channelId=10743%2C10744%2C10012&extGGDL=&order=createTime|desc%2Cstockcode|asc&isPagination=true&pageHelp.pageSize={page_size}&pageHelp.pageNo={page_num}'
    res = ss.get(url)
    df = pd.DataFrame(res.json()['result'])
    df = df[['stockcode', 'extGSJC', 'cmsOpDate', 'extWTFL', 'docTitle', 'docURL']]
    df['docURL'] = df['docURL'].apply(lambda x: x.split('/')[-1])
    return df


# 深交所问询函件总页数，需重点关注的为年报问询函
def get_sse_page_num(page_size: str = 15) -> pd.DataFrame:
    ss = requests_html.HTMLSession()
    ss.headers['Referer'] = 'http://www.sse.com.cn/disclosure/credibility/supervision/inquiries/'
    url = f'http://query.sse.com.cn/commonSoaQuery.do?siteId=28&sqlId=BS_KCB_GGLL&channelId=10743%2C10744%2C10012&extGGDL=&order=createTime|desc%2Cstockcode|asc&isPagination=true&pageHelp.pageSize={page_size}&pageHelp.pageNo=1'
    res = ss.get(url)
    return res.json()['pageHelp']['pageCount']


# 深交所问询函件总条数
def get_sse_record_count(page_size: str = 15) -> int:
    ss = requests_html.HTMLSession()
    ss.headers['Referer'] = 'http://www.sse.com.cn/disclosure/credibility/supervision/inquiries/'
    url = f'http://query.sse.com.cn/commonSoaQuery.do?siteId=28&sqlId=BS_KCB_GGLL&channelId=10743%2C10744%2C10012&extGGDL=&order=createTime|desc%2Cstockcode|asc&isPagination=true&pageHelp.pageSize={page_size}&pageHelp.pageNo=1'
    res = ss.get(url)
    return res.json()['pageHelp']['total']


# 获取所有数据
def get_sse_all() -> pd.DataFrame:
    record_count = get_sse_record_count()
    return get_sse_one_page(1, record_count)


##### ##### ##### #####
# 工具函数
def clean_str(input_str: str) -> str:
    try:
        return input_str.split('/')[3].split("'")[0]
    except:
        return ''


##### ##### ##### #####
# http://www.iwencai.com/stockpick/search?querytype=stock&w=证监会立案
# 证监会立案
# 理论上可以抓取同花顺所有数据
def get_csrc_iwc() -> pd.DataFrame:
    self_path = path.dirname(path.abspath(__file__))
    js_path = path.join(self_path, 'aes.min.js')

    ss = requests_html.HTMLSession()
    with open(js_path, 'r') as fl:
        jscontent = fl.read()
    ss.headers['Cookie'] = 'v=' + run_js(jscontent, 'v')
    url = 'http://www.iwencai.com/stockpick/search?querytype=stock&w=证监会立案'
    res = ss.get(url)
    res_df = pd.read_html(res.text, encoding='utf-8')
    df1 = res_df[4][[2, 3]]
    df1.columns = ['股票代码', '股票简称']
    df1['股票代码'] = df1['股票代码'].astype('str')
    df1['股票代码'] = df1['股票代码'].apply(lambda x: '0'*(6-len(x)) + x)
    df2 = res_df[3][[2, 3, 4, 5, 6]]
    df2.columns = ['立案调查主体', '立案调查时间', '立案调查标题', '立案调查原因', '立案调查发布时间']
    return pd.concat([df1, df2], axis=1).sort_values(by='立案调查发布时间', ascending=False).reset_index(drop=True)


# ------------------------------------------------------- Fields -------------------------------------------------------

FIELDS = {
    'Market.Enquiries': {
    },
    'Market.Investigation': {
        'investigating_organization':    '立案调查主体',
        'investigate_date':              '立案调查时间',
        'investigate_topic':             '立案调查标题',
        'investigate_reason':            '立案调查原因',
        'investigate_announcement_date': '立案调查发布时间',
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'market_inquiry_and_investigation',
        'plugin_version': '0.0.0.1',
        'tags': ['LeeXuanhe']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

def __fetch_szse_enquiries(since: datetime.datetime) -> pd.DataFrame or None:
    df_szse = None
    szse_page_count = get_szse_page_num()
    for page in range(szse_page_count):
        df_page = get_szse_one_page(page + 1)
        # Only update data that later than specified for saving time
        if df_page is not None and len(df_page) > 0:
            time_str = df_page['fhrq'][0]
            if text_auto_time(time_str) < since:
                break
        df_szse = df_page if df_szse is None else pd.concat([df_szse, df_page])
    df_szse = df_szse.reset_index(drop=True)

    df_szse['exchange'] = 'SZSE'
    df_szse['gsdm'] = df_szse['gsdm'] + '.SZSE'
    # Because the format checker expects datetime64[ns]
    # df_szse['fhrq'] = df_szse['fhrq'].apply(text_auto_time)
    df_szse['fhrq'] = pd.to_datetime(df_szse['fhrq'], format='%Y/%m/%d')

    df_szse.rename(columns={'gsdm': 'stock_identity',
                            'gsjc': 'name',
                            'fhrq': 'enquiry_date',
                            'hjlb': 'enquiry_topic',
                            'ck': 'enquiry_title'}, inplace=True)
    del df_szse['hfck']

    return df_szse


def __fetch_sse_enquiries() -> pd.DataFrame or None:
    df_sse = get_sse_all()
    df_sse = df_sse.reset_index(drop=True)

    df_sse['exchange'] = 'SSE'
    df_sse['stockcode'] = df_sse['stockcode'] + '.SSE'
    # Because the format checker expects datetime64[ns]
    # df_sse['cmsOpDate'] = df_sse['cmsOpDate'].apply(text_auto_time)
    df_sse['cmsOpDate'] = pd.to_datetime(df_sse['cmsOpDate'], format='%Y-%m-%d %H:%M:%S')

    df_sse.rename(columns={'stockcode': 'stock_identity',
                           'extGSJC': 'name',
                           'cmsOpDate': 'enquiry_date',
                           'extWTFL': 'enquiry_topic',
                           'docTitle': 'enquiry_title'}, inplace=True)
    del df_sse['docURL']

    return df_sse


def __fetch_enquiries(**kwargs) -> pd.DataFrame or None:
    result = check_execute_test_flag(**kwargs)
    if result is None:
        time_serial = kwargs.get('enquiry_date', None)
        since, until = normalize_time_serial(time_serial, default_since(), today())

        df_szse = __fetch_szse_enquiries(since)
        df_sse = __fetch_sse_enquiries()
        if df_szse is None:
            result = df_szse
        elif df_sse is None:
            result = df_szse
        else:
            result = pd.concat([df_szse, df_sse], sort=False)
    check_execute_dump_flag(result, **kwargs)

    # if result is not None:
    #     result.to_csv('all.csv')

    # result = result[result['enquiry_date'] >= since]
    # result = result[result['enquiry_date'] <= until]

    return result


# ---------------------------------------------------------------------------

def __fetch_investigations(**kwargs) -> pd.DataFrame or None:
    result = check_execute_test_flag(**kwargs)
    if result is None:
        result = get_csrc_iwc()

    if result is not None:
        result.rename(columns={'股票代码': 'stock_identity',
                               '股票简称': 'name',
                               '立案调查主体': 'investigating_organization',
                               '立案调查时间': 'investigate_date',
                               '立案调查标题': 'investigate_topic',
                               '立案调查原因': 'investigate_reason',
                               '立案调查发布时间': 'investigate_announcement_date'}, inplace=True)

        result['stock_identity'] = result['stock_identity'].apply(stock_code_to_stock_identity)
        result['investigate_date'] = pd.to_datetime(result['investigate_date'], format='%Y%m%d')
        result['investigate_announcement_date'] = pd.to_datetime(result['investigate_announcement_date'],
                                                                 format='%Y%m%d')

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == 'Market.Enquiries':
        return __fetch_enquiries(**kwargs)
    elif uri == 'Market.Investigation':
        return __fetch_investigations(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS



