import traceback

import requests_html
import pandas as pd
import time
import execjs
pd.set_option('mode.chained_assignment', None)


def run_js(js_text: str, invoke: str):
    js_env = execjs.get().name
    print('-----------------------------------------------------------------')
    print('Run java script: ')
    print('Js environment: ' + js_env)
    if js_env == 'JScript':
        print('Warning: Run JS in windows environment may cause access denied. It is recommended to use NodeJs.')
    else:
        pass
    try:
        context = execjs.compile(js_text)
        return context.call(invoke)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return None
    finally:
        print('-----------------------------------------------------------------')


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
    df = pd.DataFrame(res.json()[0]['data'])
    df['ck'] = df['ck'].apply(lambda x: clean_str(x))
    df['hfck'] = df['hfck'].apply(lambda x: clean_str(x))
    return df


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
# http://www.iwencai.com/stockpick/search?querytype=stock&w=立案
# 证监会立案
# 理论上可以抓取同花顺所有数据
def get_csrc_iwc() -> pd.DataFrame:
    ss = requests_html.HTMLSession()
    with open('./aes.min.js', 'r') as fl:
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


# df = get_szse_page_num()
# print(df)
# print('-----------------------------------------------------------------------------')
#
# df = get_szse_record_count()
# print(df)
# print('-----------------------------------------------------------------------------')
#
# df = get_szse_one_page(0)
# print(df)
# print('-----------------------------------------------------------------------------')

df = get_szse_all()
print(df)
print('-----------------------------------------------------------------------------')

df.to_csv('szse.csv')


# page_num = get_sse_page_num()
record_count = get_sse_record_count()

page = 1
df = None
while record_count > 0:
    result = get_sse_one_page(page, 100)
    df = result if df is None else pd.concat([df, result], axis=0)
    record_count -= 100
    page += 1
df.to_csv('sse.csv')

# print(df)
# print('-----------------------------------------------------------------------------')


# df = get_csrc_iwc()
# print(df)
# print('-----------------------------------------------------------------------------')

