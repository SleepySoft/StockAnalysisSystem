import time
import urllib
import random
import logging
import requests
import datetime
from os import sys, path, makedirs

from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QDateTimeEdit, QCheckBox

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.ui_utility import *
    from Utiltity.time_utility import *
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.ui_utility import *
    from Utiltity.time_utility import *
finally:
    pass


# -------------------------------------------- class AnnouncementDownloader --------------------------------------------

# -----------------------------------------------------------
# Get code from : https://github.com/gaodechen/cninfo_process
# -----------------------------------------------------------

User_Agent = [
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0"
]


headers = {'Accept': 'application/json, text/javascript, */*; q=0.01',
           "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
           "Accept-Encoding": "gzip, deflate",
           "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-HK;q=0.6,zh-TW;q=0.5",
           'Host': 'www.cninfo.com.cn',
           'Origin': 'http://www.cninfo.com.cn',
           'Referer': 'http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice',
           'X-Requested-With': 'XMLHttpRequest'
           }


class AnnouncementDownloader:
    def __init__(self):
        pass

    @staticmethod
    def format_query_time_range(time_range: any) -> str:
        if time_range is None:
            return AnnouncementDownloader.format_query_time_range((years_ago(3), now()))
        if isinstance(time_range, str):
            return time_range
        if isinstance(time_range, datetime.datetime):
            return AnnouncementDownloader.format_query_time_range((time_range, time_range))
        if not isinstance(time_range, (tuple, list)):
            return AnnouncementDownloader.format_query_time_range(None)
        if len(time_range) == 0:
            return AnnouncementDownloader.format_query_time_range(None)
        if len(time_range) == 1:
            return AnnouncementDownloader.format_query_time_range((time_range[0], time_range[0]))
        since = time_range[0]
        until = time_range[1]
        return '%s+~+%s' % (since.strftime('%Y-%m-%d'), until.strftime('%Y-%m-%d'))

    @staticmethod
    def build_query_for_szse_annual_report(page: int, stock: str, time_range: any = None):
        query_path = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
        headers['User-Agent'] = random.choice(User_Agent)  # 定义User_Agent
        time_range = AnnouncementDownloader.format_query_time_range(time_range)

        query = {'pageNum': page,  # 页码
                 'pageSize': 30,
                 'tabName': 'fulltext',
                 'column': 'szse',  # 深交所
                 'stock': stock,
                 'searchkey': '',
                 'secid': '',
                 'plate': 'sz',
                 'category': 'category_ndbg_szsh;',  # 年度报告
                 'trade': '',
                 'seDate': time_range,
                 }

        namelist = requests.post(query_path, headers=headers, data=query)
        return namelist.json()['announcements']

    @staticmethod
    def build_query_for_sse_annual_report(page: int, stock: str, time_range: any = None):
        query_path = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
        headers['User-Agent'] = random.choice(User_Agent)  # 定义User_Agent
        time_range = AnnouncementDownloader.format_query_time_range(time_range)

        query = {'pageNum': page,  # 页码
                 'pageSize': 30,
                 'tabName': 'fulltext',
                 'column': 'sse',
                 'stock': stock,
                 'searchkey': '',
                 'secid': '',
                 'plate': 'sh',
                 'category': 'category_ndbg_szsh;',  # 年度报告
                 'trade': '',
                 'seDate': time_range
                 }

        namelist = requests.post(query_path, headers=headers, data=query)
        return namelist.json()['announcements']  # json中的年度报告信息

    @staticmethod
    def execute_download(page_data, include_filter: [str] or None = None, exclude_filter: [str] or None = None):
        if page_data is None:
            return

        # download_headers = {
        #     'Accept': 'application/json, text/javascript, */*; q=0.01',
        #     'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        #     'Accept-Encoding': 'gzip, deflate',
        #     'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-HK;q=0.6,zh-TW;q=0.5',
        #     'Host': 'www.cninfo.com.cn',
        #     'Origin': 'http://www.cninfo.com.cn'
        # }
        # download_headers['User-Agent'] = random.choice(User_Agent)
        download_path = 'http://static.cninfo.com.cn/'

        for page in page_data:
            title = page['announcementTitle']

            allowed = False
            if include_filter is not None and len(include_filter) > 0:
                for inc in include_filter:
                    if inc in title:
                        allowed = True
                        break
            else:
                allowed = True

            if exclude_filter is not None and len(exclude_filter) > 0:
                for exc in exclude_filter:
                    if exc in title:
                        allowed = False
                        break
            print('Announcement <<' + title + '>> ' + ('Allowed' if allowed else 'Ignore'))
            if not allowed:
                continue

            download = download_path + page["adjunctUrl"]
            file_name = AnnouncementDownloader.format_download_path(page)

            if '*' in file_name:
                file_name = file_name.replace('*', '')

            time.sleep(random.random() * 2)
            r = requests.get(download)

            f = open(file_name, "wb")
            f.write(r.content)
            f.close()

    @staticmethod
    def format_download_path(page) -> str:
        file_name = page['secName'] + '_' + page['announcementTitle'] + '.pdf'
        file_path = path.join(root_path, page['secCode'])
        makedirs(file_path, exist_ok=True)
        return path.join(file_path, file_name)

    # ----------------------------------------- Interface -----------------------------------------

    @staticmethod
    def download_annual_report(stock_identity: str or list, time_range: any = None):
        if not isinstance(stock_identity, (list, tuple)):
            stock_identity = [stock_identity]
        for s in stock_identity:
            if s.endwith('.SSE'):
                s = s[: -4]
                page_data = AnnouncementDownloader.build_query_for_sse_annual_report(s, time_range)
            elif s.endwith('.SZSE'):
                s = s[: -5]
                page_data = AnnouncementDownloader.build_query_for_szse_annual_report(s, time_range)
            else:
                exchange = get_stock_exchange(s)
                if exchange == 'SSE':
                    page_data = AnnouncementDownloader.build_query_for_sse_annual_report(s, time_range)
                elif exchange == 'SZSE':
                    page_data = AnnouncementDownloader.build_query_for_szse_annual_report(s, time_range)
                else:
                    page_data = AnnouncementDownloader.build_query_for_sse_annual_report(s, time_range)
            AnnouncementDownloader.execute_download(page_data, 
                                                    include_filter=['年年度报告'],
                                                    exclude_filter=['确认意见'])


# allowed_list = [
#     '2018年年度报告（更新后）',
#     '2018年年度报告',
#     '2017年年度报告（更新后）',
#     '2017年年度报告',
#     '2016年年度报告（更新后）',
#     '2016年年度报告',
# ]
# allowed_list_2 = [
#     '招股书',
#     '招股说明书',
#     '招股意向书',
# ]
#
# exclude = [
#     '确认意见'
# ]


# ----------------------------------------------------------------------------------------------------------------------

class AnnouncementDownloaderUi(QWidget):
    def __init__(self):
        super(AnnouncementDownloaderUi, self).__init__()

        # Timer for update stock list
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # Ui component
        self.__combo_name = QComboBox()
        self.__button_download = QPushButton('确定')
        self.__check_annual_report = QCheckBox('年报')
        self.__check_customize = QCheckBox('自定义')

        self.__datetime_since = QDateTimeEdit(QDateTime.currentDateTime())
        self.__datetime_until = QDateTimeEdit(QDateTime.currentDateTime())

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addLayout(horizon_layout([QLabel('股票代码'), self.__combo_name]))
        main_layout.addLayout(horizon_layout([QLabel('报告起始'), self.__datetime_since]))
        main_layout.addLayout(horizon_layout([QLabel('报告截至'), self.__datetime_until]))
        main_layout.addLayout(horizon_layout([QLabel('报告类型'), self.__datetime_until]))

    def __config_control(self):
        self.__button_draw.clicked.connect(self.on_button_draw)

    def on_timer(self):
        # Check stock list ready and update combobox
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        if data_utility.stock_cache_ready():
            stock_list = data_utility.get_stock_list()
            for stock_identity, stock_name in stock_list:
                self.__combo_name.addItem(stock_identity + ' | ' + stock_name, stock_identity)
            self.__timer.stop()

    def on_button_download(self):
        pass


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'efa60977-65e9-4ecf-9271-7c6e629da399',
        'plugin_name': 'ReportDownloader',
        'plugin_version': '0.0.0.1',
        'tags': ['Announcement', 'Report', 'Finance Report', 'Annual Report', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return ['widget']


# ----------------------------------------------------------------------------------------------------------------------

sasEntry = None


def init(sas: StockAnalysisSystem) -> bool:
    try:
        global sasEntry
        sasEntry = sas
    except Exception as e:
        pass
    finally:
        pass
    return True


def widget(parent: QWidget) -> (QWidget, dict):
    return AnnouncementDownloaderUi(sasEntry.get_data_hub_entry()), {'name': 'Announcement Downloader', 'show': False}


















