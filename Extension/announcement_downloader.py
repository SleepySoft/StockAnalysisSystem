import logging
import requests
import random
import time
import urllib
import matplotlib
from pylab import mpl
from os import sys, path
from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QFileDialog, QComboBox, QVBoxLayout

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Analyzer.AnalyzerUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from Analyzer.AnalyzerUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
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

    def execute_download(self, queries, include: [str], exclude: [str]):
        if queries is None:
            return

        headers = {'Accept': 'application/json, text/javascript, */*; q=0.01',
                   "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                   "Accept-Encoding": "gzip, deflate",
                   "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-HK;q=0.6,zh-TW;q=0.5",
                   'Host': 'www.cninfo.com.cn',
                   'Origin': 'http://www.cninfo.com.cn'
                   }

        for i in queries:
            allowed_list = [
                '2018年年度报告（更新后）',
                '2018年年度报告',
                '2017年年度报告（更新后）',
                '2017年年度报告',
                '2016年年度报告（更新后）',
                '2016年年度报告',
            ]
            allowed_list_2 = [
                '招股书',
                '招股说明书',
                '招股意向书',
            ]
            title = i['announcementTitle']
            allowed = title in allowed_list
            if '确认意见' in title:
                return
            for item in allowed_list_2:
                if item in title:
                    allowed = True
                    break
            if allowed:
                download = download_path + i["adjunctUrl"]
                name = i["secCode"] + '_' + i['secName'] + '_' + i['announcementTitle'] + '.pdf'
                if '*' in name:
                    name = name.replace('*', '')
                file_path = saving_path + name
                time.sleep(random.random() * 2)

                headers['User-Agent'] = random.choice(User_Agent)
                r = requests.get(download)

                f = open(file_path, "wb")
                f.write(r.content)
                f.close()
            else:
                continue

    def format_download_path(self, queries) -> str:
        pass


# ----------------------------------------------------------------------------------------------------------------------

class AnnouncementDownloaderUi(QWidget):
    def __init__(self, datahub_entry: DataHubEntry):
        super(AnnouncementDownloaderUi, self).__init__()

        # ---------------- ext var ----------------

        self.__data_hub = datahub_entry
        self.__data_center = self.__data_hub.get_data_center() if self.__data_hub is not None else None
        self.__data_utility = self.__data_hub.get_data_utility() if self.__data_hub is not None else None

        # ------------- plot resource -------------

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

    def __config_control(self):
        self.__button_draw.clicked.connect(self.on_button_draw)

    def on_button_draw(self):
        self.plot()


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


















