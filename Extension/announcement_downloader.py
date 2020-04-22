import time
import urllib
import random
import logging
import requests
import datetime
from os import sys, path, makedirs

from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QDateTimeEdit, QCheckBox, QLineEdit, \
    QRadioButton

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.ui_utility import *
    from Utiltity.task_queue import *
    from Utiltity.time_utility import *
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.ui_utility import *
    from Utiltity.task_queue import *
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
    def get_szse_annual_report_pages(page: int, stock: str, time_range: any = None):
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
    def get_sse_annual_report_pages(page: int, stock: str, time_range: any = None):
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
    def execute_download(report_pages, include_filter: [str] or None = None,
                         exclude_filter: [str] or None = None, quit_flag: [bool] = None):

        if report_pages is None:
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

        for page in report_pages:
            if quit_flag is not None and quit_flag[0]:
                break
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
            print('Announcement <<' + title + '>> : ' + ('Allowed' if allowed else 'Ignore'))
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
        file_path = path.join(root_path, 'Download', 'report', page['secCode'])
        makedirs(file_path, exist_ok=True)
        return path.join(file_path, file_name)

    # ----------------------------------------- Interface -----------------------------------------

    @staticmethod
    def download_annual_report(stock_identity: str or list, time_range: any = None, quit_flag: [bool] = None):
        if not isinstance(stock_identity, (list, tuple)):
            stock_identity = [stock_identity]
        for s in stock_identity:
            if s.endswith('.SSE'):
                s = s[: -4]
                page_data = AnnouncementDownloader.get_sse_annual_report_pages(1, s, time_range)
            elif s.endswith('.SZSE'):
                s = s[: -5]
                page_data = AnnouncementDownloader.get_szse_annual_report_pages(1, s, time_range)
            else:
                exchange = get_stock_exchange(s)
                if exchange == 'SSE':
                    page_data = AnnouncementDownloader.get_sse_annual_report_pages(1, s, time_range)
                elif exchange == 'SZSE':
                    page_data = AnnouncementDownloader.get_szse_annual_report_pages(1, s, time_range)
                else:
                    page_data = AnnouncementDownloader.get_sse_annual_report_pages(1, s, time_range)
            AnnouncementDownloader.execute_download(page_data, 
                                                    include_filter=['年年度报告'],
                                                    exclude_filter=['确认意见', '摘要'],
                                                    quit_flag=quit_flag)


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

# --------------------------------------------- UpdateTask ---------------------------------------------

class AnnouncementDownloadTask(TaskQueue.Task):
    REPORT_TYPE_NONE = 0
    REPORT_TYPE_ANNUAL = 1

    def __init__(self):
        super(AnnouncementDownloadTask, self).__init__('AnnouncementDownloadTask')

        self.__quit_flag = [False]

        # Parameters
        self.securities = ''
        self.period_since = None
        self.period_until = None
        self.filter_include = []
        self.filter_exclude = []
        self.report_type = AnnouncementDownloadTask.REPORT_TYPE_ANNUAL

    def run(self):
        try:
            self.__execute_update()
        except Exception as e:
            print(e)
            print('Continue...')
        finally:
            print('Finished')
        
    def quit(self):
        self.__quit_flag[0] = True

    def identity(self) -> str:
        return 'Download Report: ' + self.securities

    def __execute_update(self):
        if self.report_type == AnnouncementDownloadTask.REPORT_TYPE_ANNUAL:
            AnnouncementDownloader.download_annual_report(self.securities, (self.period_since, self.period_until),
                                                          self.__quit_flag)
        else:
            pass


# --------------------------------------- AnnouncementDownloaderUi ---------------------------------------

DEFAULT_INFO = '''
1.本扩展用以从巨朝网下载上市公司的各种公开报告
2.如果选择“自定义”，请自行设置关键字以根据报告标题进行过滤
3.下载任务会占用系统工作队列，请在View->Task中管理下载任务
3.默认下载路径为当前目录下Download/report/
4.如果选择时间范围过大或股票过多，可能会被网站BAN
5.下载代码来自：https://github.com/gaodechen/cninfo_process
6.已知缺陷：暂时只能取第一页的报告，后面解决
'''


class AnnouncementDownloaderUi(QWidget):
    def __init__(self, datahub_entry, task_manager):
        super(AnnouncementDownloaderUi, self).__init__()

        # ---------------- ext var ----------------

        self.__data_hub = datahub_entry
        self.__data_center = self.__data_hub.get_data_center() if self.__data_hub is not None else None
        self.__data_utility = self.__data_hub.get_data_utility() if self.__data_hub is not None else None
        self.__task_manager = task_manager

        # Timer for update stock list
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # Ui component
        self.__combo_name = QComboBox()
        self.__radio_annual_report = QRadioButton('年报')
        self.__radio_customize_filter = QRadioButton('自定义')
        self.__line_filter_include = QLineEdit()
        self.__line_filter_exclude = QLineEdit()
        self.__button_download = QPushButton('确定')

        self.__datetime_since = QDateTimeEdit(QDateTime.currentDateTime().addYears(-3))
        self.__datetime_until = QDateTimeEdit(QDateTime.currentDateTime())

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addLayout(horizon_layout([QLabel('股票代码'), self.__combo_name], [1, 10]))
        main_layout.addLayout(horizon_layout([QLabel('报告起始'), self.__datetime_since], [1, 10]))
        main_layout.addLayout(horizon_layout([QLabel('报告截止'), self.__datetime_until], [1, 10]))
        main_layout.addLayout(horizon_layout([QLabel('报告类型'), self.__radio_annual_report,
                                                                  self.__radio_customize_filter], [1, 5, 5]))
        main_layout.addLayout(horizon_layout([QLabel('包含词条(以,分隔)'), self.__line_filter_include], [1, 10]))
        main_layout.addLayout(horizon_layout([QLabel('排除词条(以,分隔)'), self.__line_filter_exclude], [1, 10]))
        main_layout.addWidget(QLabel(DEFAULT_INFO))
        main_layout.addWidget(self.__button_download)

    def __config_control(self):
        self.__combo_name.setEditable(True)
        self.__radio_annual_report.setChecked(True)
        self.__line_filter_include.setEnabled(False)
        self.__line_filter_exclude.setEnabled(False)
        self.__radio_annual_report.clicked.connect(self.on_radio_report_type)
        self.__radio_customize_filter.clicked.connect(self.on_radio_report_type)
        self.__button_download.clicked.connect(self.on_button_download)

    def on_timer(self):
        # Check stock list ready and update combobox
        if self.__data_utility is not None:
            if self.__data_utility.stock_cache_ready():
                stock_list = self.__data_utility.get_stock_list()
                for stock_identity, stock_name in stock_list:
                    self.__combo_name.addItem(stock_identity + ' | ' + stock_name, stock_identity)
                self.__timer.stop()

    def on_radio_report_type(self):
        if self.__radio_annual_report.isChecked():
            self.__line_filter_include.setEnabled(False)
            self.__line_filter_exclude.setEnabled(False)
        else:
            self.__line_filter_include.setEnabled(True)
            self.__line_filter_exclude.setEnabled(True)

    def on_button_download(self):
        input_securities = self.__combo_name.currentText()
        if '|' in input_securities:
            input_securities = input_securities.split('|')[0].strip()

        task = AnnouncementDownloadTask()
        task.securities = input_securities
        task.period_since = self.__datetime_since.dateTime().toPyDateTime()
        task.period_until = self.__datetime_until.dateTime().toPyDateTime()
        task.filter_include = self.__line_filter_include.text().split(',')
        task.filter_exclude = self.__line_filter_exclude.text().split(',')
        task.report_type = \
            AnnouncementDownloadTask.REPORT_TYPE_ANNUAL \
                if self.__radio_annual_report.isChecked() else \
            AnnouncementDownloadTask.REPORT_TYPE_NONE

        if self.__task_manager is not None:
            self.__task_manager.append_task(task)
        else:
            task.run()


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


def init(sas) -> bool:
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


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(AnnouncementDownloaderUi(None, None))
    dlg.exec()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass















