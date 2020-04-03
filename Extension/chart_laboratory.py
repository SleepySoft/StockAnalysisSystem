import logging
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


# ----------------------------------------------------------------------------------------------------------------------


pyplot_logger = logging.getLogger('matplotlib')
pyplot_logger.setLevel(level=logging.INFO)


# https://stackoverflow.com/questions/12459811/how-to-embed-matplotlib-in-pyqt-for-dummies
# https://stackoverflow.com/questions/42373104/since-matplotlib-finance-has-been-deprecated-how-can-i-use-the-new-mpl-finance

class ChartLab(QWidget):
    def __init__(self, datahub_entry: DataHubEntry):
        super(ChartLab, self).__init__()

        # ---------------- ext var ----------------

        self.__data_hub = datahub_entry
        self.__data_center = self.__data_hub.get_data_center() if self.__data_hub is not None else None
        self.__data_utility = self.__data_hub.get_data_utility() if self.__data_hub is not None else None

        self.__inited = False
        self.__plot_table = {}

        # ------------- plot resource -------------

        self.__figure = plt.figure()
        self.__canvas = FigureCanvas(self.__figure)

        # -------------- ui resource --------------

        self.__button_draw = QPushButton('Draw')

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(1280, 800)

        main_layout.addWidget(self.__canvas)
        main_layout.addWidget(self.__button_draw)

    def __config_control(self):
        self.__button_draw.clicked.connect(self.on_button_draw)

    def on_button_draw(self):
        self.plot()

    def plot(self):
        self.plot_histogram_statistics()

    def plot_histogram_statistics(self):
        # --------------------------- The Data and Period We Want to Check ---------------------------

        stock = ''
        period = (text_auto_time('2018-12-01'), text_auto_time('2018-12-31'))

        # --------------------------------------- Query Pattern --------------------------------------

        fields_balance_sheet = ['货币资金', '资产总计', '负债合计',
                                '短期借款', '一年内到期的非流动负债', '其他流动负债',
                                '长期借款', '应付债券', '其他非流动负债', '流动负债合计',
                                '应收票据', '应收账款', '其他应收款', '预付款项',
                                '交易性金融资产', '可供出售金融资产',
                                '在建工程', '商誉', '固定资产']
        fields_income_statement = ['营业收入', '营业总收入', '减:营业成本', '息税前利润']

        df, result = batch_query_readable_annual_report_pattern(
            self.__data_hub, stock, period, fields_balance_sheet, fields_income_statement)
        if result is not None:
            return result

        # df_balance_sheet, result = query_readable_annual_report_pattern(
        #     self.__data_hub, 'Finance.BalanceSheet', stock, period, fields_balance_sheet)
        # if result is not None:
        #     print('Data Error')
        #
        # df_income_statement, result = query_readable_annual_report_pattern(
        #     self.__data_hub, 'Finance.IncomeStatement', stock, period, fields_income_statement)
        # if result is not None:
        #     print('Data Error')

        # -------------------------------- Merge and Pre-processing --------------------------------

        # df = pd.merge(df_balance_sheet,
        #               df_income_statement,
        #               how='left', on=['stock_identity', 'period'])

        df = df.sort_values('period')
        df = df.reset_index()
        df = df.fillna(0)
        df = df.replace(0, 1)

        # ------------------------------------- Calc and Plot -------------------------------------

        mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        mpl.rcParams['axes.unicode_minus'] = False

        # font = matplotlib.font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttf')
        # mpl.rcParams['axes.unicode_minus'] = False

        df['应收款'] = df['应收账款'] + df['应收票据']
        df['净资产'] = df['资产总计'] - df['负债合计']
        df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
        df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']
        df['金融资产'] = df['交易性金融资产'] + df['可供出售金融资产']

        # s1 = df['货币资金'] / df['有息负债']
        # s1 = s1.apply(lambda x: x if x < 10 else 10)
        # plt.subplot(2, 1, 1)
        # s1.hist(bins=100)
        # plt.title('货币资金/有息负债')
        #
        # s2 = df['有息负债'] / df['资产总计']
        # plt.subplot(2, 1, 2)
        # s2.hist(bins=100)
        # plt.title('有息负债/资产总计')

        # s1 = df['应收款'] / df['营业收入']
        # s1 = s1.apply(lambda x: x if x < 2 else 2)
        # plt.subplot(4, 1, 1)
        # s1.hist(bins=100)
        # plt.title('应收款/营业收入')
        #
        # s2 = df['其他应收款'] / df['营业收入']
        # s2 = s2.apply(lambda x: x if x < 1 else 1)
        # plt.subplot(4, 1, 2)
        # s2.hist(bins=100)
        # plt.title('其他应收款/营业收入')
        #
        # s3 = df['预付款项'] / df['营业收入']
        # s3 = s3.apply(lambda x: x if x < 1 else 1)
        # plt.subplot(4, 1, 3)
        # s3.hist(bins=100)
        # plt.title('预付款项/营业收入')
        #
        # s4 = df['预付款项'] / df['减:营业成本']
        # s4 = s4.apply(lambda x: x if x < 1 else 1)
        # plt.subplot(4, 1, 4)
        # s4.hist(bins=100)
        # plt.title('预付款项/营业成本')

        # s1 = df['商誉'] / df['净资产']
        # s1 = s1.apply(lambda x: (x if x < 1 else 1) if x > 0 else 0)
        # plt.subplot(3, 1, 1)
        # s1.hist(bins=100)
        # plt.title('商誉/净资产')
        #
        # s2 = df['在建工程'] / df['净资产']
        # s2 = s2.apply(lambda x: (x if x < 1 else 1) if x > 0 else 0)
        # plt.subplot(3, 1, 2)
        # s2.hist(bins=100)
        # plt.title('在建工程/净资产')
        #
        # s2 = df['在建工程'] / df['资产总计']
        # s2 = s2.apply(lambda x: (x if x < 1 else 1) if x > 0 else 0)
        # plt.subplot(3, 1, 3)
        # s2.hist(bins=100)
        # plt.title('在建工程/资产总计')

        # s1 = df['固定资产'] / df['资产总计']
        # s1 = s1.apply(lambda x: (x if x < 1 else 1) if x > 0 else 0)
        # plt.subplot(2, 1, 1)
        # s1.hist(bins=100)
        # plt.title('固定资产/资产总计')
        #
        # s2 = df['息税前利润'] / df['固定资产']
        # s2 = s2.apply(lambda x: (x if x < 10 else 10) if x > -10 else -10)
        # plt.subplot(2, 1, 2)
        # s2.hist(bins=100)
        # plt.title('息税前利润/固定资产')

        self.plot_proportion([
            ChartLab.PlotItem('固定资产', '资产总计', 0, 1),
            ChartLab.PlotItem('息税前利润', '固定资产', -10, 10),
        ], text_auto_time('2018-12-31'))

        self.repaint()

    class PlotItem:
        def __init__(self, num: str, den: str,
                     lower: float or None = None, upper:float or None = None,
                     bins: int = 100):
            self.numerator = num
            self.denominator = den
            self.limit_lower = lower
            self.limit_upper = upper
            self.plot_bins = bins

    def plot_proportion(self, plot_set: [PlotItem], period: datetime.datetime):
        df = self.prepare_plot_data(plot_set, period)

        plot_count = len(plot_set)
        for plot_index in range(plot_count):
            plot_item = plot_set[plot_index]
            s = df[plot_item.numerator] / df[plot_item.denominator]
            if plot_item.limit_lower is not None:
                s = s.apply(lambda x: max(x, plot_item.limit_lower))
            if plot_item.limit_upper is not None:
                s = s.apply(lambda x: min(x, plot_item.limit_upper))
            plt.subplot(plot_count, 1, plot_index + 1)
            s.hist(bins=plot_item.plot_bins)
            plt.title(plot_item.numerator + '/' + plot_item.denominator)

    def prepare_plot_data(self, plot_set: [PlotItem], period: datetime.datetime) -> pd.DataFrame:
        fields = []
        for plot_item in plot_set:
            fields.append(plot_item.numerator)
            fields.append(plot_item.denominator)
        fields = list(set(fields))
        return self.__data_utility.auto_query(
            '', (period - datetime.timedelta(days=1), period), fields, ['stock_identity', 'period'])


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '29ae0dea-fbb6-490e-b1c8-f5dd206bf661',
        'plugin_name': 'ChartLab',
        'plugin_version': '0.0.0.1',
        'tags': ['Chart', 'Test', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return ['widget']
    # return [
    #     'period',
    #     'thread',
    #     'widget',
    # ]


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
    return ChartLab(sasEntry.get_data_hub_entry()), {'name': 'Chart Lab', 'show': False}


















