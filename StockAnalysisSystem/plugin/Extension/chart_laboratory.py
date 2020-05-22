import logging
import matplotlib as mpl
from os import sys, path
from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QFileDialog, QComboBox, QVBoxLayout, \
    QApplication, QLabel, QRadioButton, QHBoxLayout

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

root_path = path.dirname(path.dirname(path.abspath(__file__)))

from StockAnalysisSystem.core.FactorEntry import FactorCenter
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.Utiltity.securities_selector import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


# ----------------------------------------------------------------------------------------------------------------------


pyplot_logger = logging.getLogger('matplotlib')
pyplot_logger.setLevel(level=logging.INFO)


# https://stackoverflow.com/questions/12459811/how-to-embed-matplotlib-in-pyqt-for-dummies
# https://stackoverflow.com/questions/42373104/since-matplotlib-finance-has-been-deprecated-how-can-i-use-the-new-mpl-finance


TIP_PARALLEL_COMPARISON = '''横向比较：将同一报告期内所有的或某行业的股票的同一参数进行比较，将其分布绘制在直方图上'''
TIP_LONGITUDINAL_COMPARISON = '''纵向比较：将某一股票所有报告期内的某一参数绘制在折线图上，以查看其发展趋势'''
TIP_LIMIT_UPPER_LOWER = '''在直方图中，某些极端值会拉长坐标轴，导致重要部分显示不清晰；
这种情况可以设置上下限将所有数值限制到某一范围内，使得重要数据更为突出'''
TIP_BUTTON_SHOW = '''显示当然绘制的图表所依赖的数据'''


class ChartLab(QWidget):
    def __init__(self, datahub_entry: DataHubEntry, factor_center: FactorCenter):
        super(ChartLab, self).__init__()

        # ---------------- ext var ----------------

        self.__data_hub = datahub_entry
        self.__factor_center = factor_center
        self.__data_center = self.__data_hub.get_data_center() if self.__data_hub is not None else None
        self.__data_utility = self.__data_hub.get_data_utility() if self.__data_hub is not None else None

        self.__inited = False
        self.__plot_table = {}
        self.__paint_data = None

        # ------------- plot resource -------------

        self.__figure = plt.figure()
        self.__canvas = FigureCanvas(self.__figure)

        # -------------- ui resource --------------

        self.__data_frame_widget = None

        self.__combo_factor = QComboBox()
        self.__label_comments = QLabel('')

        # Parallel comparison
        self.__radio_parallel_comparison = QRadioButton('横向比较')
        self.__combo_year = QComboBox()
        self.__combo_quarter = QComboBox()
        self.__combo_industry = QComboBox()

        # Longitudinal comparison
        self.__radio_longitudinal_comparison = QRadioButton('纵向比较')
        self.__combo_stock = SecuritiesSelector(self.__data_utility)

        # Limitation
        self.__line_lower = QLineEdit('')
        self.__line_upper = QLineEdit('')

        self.__button_draw = QPushButton('绘图')
        self.__button_show = QPushButton('数据')

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(1280, 800)

        bottom_layout = QHBoxLayout()
        main_layout.addWidget(self.__canvas, 99)
        main_layout.addLayout(bottom_layout, 1)

        group_box, group_layout = create_v_group_box('因子')
        bottom_layout.addWidget(group_box, 2)

        group_layout.addWidget(self.__combo_factor)
        group_layout.addWidget(self.__label_comments)

        group_box, group_layout = create_v_group_box('比较方式')
        bottom_layout.addWidget(group_box, 2)

        line = QHBoxLayout()
        line.addWidget(self.__radio_parallel_comparison, 1)
        line.addWidget(self.__combo_industry, 5)
        line.addWidget(self.__combo_year, 5)
        line.addWidget(self.__combo_quarter, 5)
        group_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(self.__radio_longitudinal_comparison, 1)
        line.addWidget(self.__combo_stock, 10)
        group_layout.addLayout(line)

        group_box, group_layout = create_v_group_box('范围限制')
        bottom_layout.addWidget(group_box, 1)

        line = QHBoxLayout()
        line.addWidget(QLabel('下限'))
        line.addWidget(self.__line_lower)
        group_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(QLabel('上限'))
        line.addWidget(self.__line_upper)
        group_layout.addLayout(line)

        col = QVBoxLayout()
        col.addWidget(self.__button_draw)
        col.addWidget(self.__button_show)
        bottom_layout.addLayout(col, 1)

    def __config_control(self):
        for year in range(now().year, 1989, -1):
            self.__combo_year.addItem(str(year), str(year))
        self.__combo_year.setCurrentIndex(1)

        self.__combo_quarter.addItem('一季报', '03-31')
        self.__combo_quarter.addItem('中报', '06-30')
        self.__combo_quarter.addItem('三季报', '09-30')
        self.__combo_quarter.addItem('年报', '12-31')
        self.__combo_quarter.setCurrentIndex(3)

        self.__combo_industry.addItem('全部', '全部')
        identities = self.__data_utility.get_all_industries()
        for identity in identities:
            self.__combo_industry.addItem(identity, identity)

        if self.__factor_center is not None:
            factors = self.__factor_center.get_all_factors()
            for fct in factors:
                self.__combo_factor.addItem(fct, fct)
        self.on_factor_updated(0)

        self.__combo_stock.setEnabled(False)
        self.__radio_parallel_comparison.setChecked(True)

        self.__radio_parallel_comparison.setToolTip(TIP_PARALLEL_COMPARISON)
        self.__radio_longitudinal_comparison.setToolTip(TIP_LONGITUDINAL_COMPARISON)
        self.__line_lower.setToolTip(TIP_LIMIT_UPPER_LOWER)
        self.__line_upper.setToolTip(TIP_LIMIT_UPPER_LOWER)
        self.__button_show.setToolTip(TIP_BUTTON_SHOW)

        self.__button_draw.clicked.connect(self.on_button_draw)
        self.__button_show.clicked.connect(self.on_button_show)

        self.__combo_factor.currentIndexChanged.connect(self.on_factor_updated)
        self.__radio_parallel_comparison.clicked.connect(self.on_radio_comparison)
        self.__radio_longitudinal_comparison.clicked.connect(self.on_radio_comparison)

        mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        mpl.rcParams['axes.unicode_minus'] = False

    def on_factor_updated(self, value):
        self.__line_lower.setText('')
        self.__line_upper.setText('')
        factor = self.__combo_factor.itemData(value)
        comments = self.__factor_center.get_factor_comments(factor)
        self.__label_comments.setText(comments)

    def on_button_draw(self):
        factor = self.__combo_factor.currentData()
        lower = str2float_safe(self.__line_lower.text(), None)
        upper = str2float_safe(self.__line_upper.text(), None)

        if self.__radio_parallel_comparison.isChecked():
            year = self.__combo_year.currentData()
            month_day = self.__combo_quarter.currentData()
            period = year + '-' + month_day
            industry = self.__combo_industry.currentData()
            self.plot_factor_parallel_comparison(factor, industry, text_auto_time(period), lower, upper)
        else:
            securities = self.__combo_stock.get_input_securities()
            self.plot_factor_longitudinal_comparison(factor, securities)

    def on_button_show(self):
        if self.__data_frame_widget is not None and \
                self.__data_frame_widget.isVisible():
            self.__data_frame_widget.close()
        if self.__paint_data is not None:
            self.__data_frame_widget = DataFrameWidget(self.__paint_data)
            self.__data_frame_widget.show()

    def on_radio_comparison(self):
        if self.__radio_parallel_comparison.isChecked():
            self.__combo_year.setEnabled(True)
            self.__combo_quarter.setEnabled(True)
            self.__line_lower.setEnabled(True)
            self.__line_upper.setEnabled(True)
            self.__combo_stock.setEnabled(False)
        else:
            self.__combo_year.setEnabled(False)
            self.__combo_quarter.setEnabled(False)
            self.__line_lower.setEnabled(False)
            self.__line_upper.setEnabled(False)
            self.__combo_stock.setEnabled(True)

    # ---------------------------------------------------------------------------------------

    def plot_factor_parallel_comparison(self, factor: str, industry: str, period: datetime.datetime,
                                        lower: float, upper: float):
        identities = ''
        if industry != '全部':
            identities = self.__data_utility.get_industry_stocks(industry)
        df = self.__data_center.query_from_factor('Factor.Finance', identities, (period, period),
                                                  fields=[factor], readable=True)

        s1 = df[factor]
        if lower is not None and upper is not None:
            s1 = s1.apply(lambda x: (x if x < upper else upper) if x > lower else lower)
        elif lower is not None:
            s1 = s1.apply(lambda x: x if x > lower else lower)
        elif upper is not None:
            s1 = s1.apply(lambda x: x if x < upper else upper)

        plt.clf()
        plt.subplot(1, 1, 1)
        s1.hist(bins=100)
        plt.title(factor)

        self.__canvas.draw()
        self.__canvas.flush_events()

        self.__paint_data = df
        self.__paint_data.sort_values(factor, inplace=True)

    def plot_factor_longitudinal_comparison(self, factor: str, securities: str):
        df = self.__data_center.query_from_factor('Factor.Finance', securities, None,
                                                  fields=[factor], readable=True)
        # Only for annual report
        df = df[df['period'].dt.month == 12]
        df['报告期'] = df['period']
        df.set_index('报告期', inplace=True)

        s1 = df[factor]

        plt.clf()
        plt.subplot(1, 1, 1)
        s1.plot.line()
        plt.title(factor)

        self.__canvas.draw()
        self.__canvas.flush_events()

        self.__paint_data = df
        self.__paint_data.sort_values('period', ascending=False, inplace=True)

    # ---------------------------------------------------------------------------------------

    def plot(self):
        self.plot_histogram_statistics()

    def plot_histogram_statistics(self):
        # --------------------------- The Data and Period We Want to Check ---------------------------

        stock = ''
        period = (text_auto_time('2018-12-01'), text_auto_time('2018-12-31'))

        # --------------------------------------- Query Pattern --------------------------------------

        # fields_balance_sheet = ['货币资金', '资产总计', '负债合计',
        #                         '短期借款', '一年内到期的非流动负债', '其他流动负债',
        #                         '长期借款', '应付债券', '其他非流动负债', '流动负债合计',
        #                         '应收票据', '应收账款', '其他应收款', '预付款项',
        #                         '交易性金融资产', '可供出售金融资产',
        #                         '在建工程', '商誉', '固定资产']
        # fields_income_statement = ['营业收入', '营业总收入', '减:营业成本', '息税前利润']
        #
        # df, result = batch_query_readable_annual_report_pattern(
        #     self.__data_hub, stock, period, fields_balance_sheet, fields_income_statement)
        # if result is not None:
        #     return result

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

        # df = df.sort_values('period')
        # df = df.reset_index()
        # df = df.fillna(0)
        # df = df.replace(0, 1)

        # ------------------------------------- Calc and Plot -------------------------------------

        mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        mpl.rcParams['axes.unicode_minus'] = False

        # font = matplotlib.font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttf')
        # mpl.rcParams['axes.unicode_minus'] = False

        # df['应收款'] = df['应收账款'] + df['应收票据']
        # df['净资产'] = df['资产总计'] - df['负债合计']
        # df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
        # df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']
        # df['金融资产'] = df['交易性金融资产'] + df['可供出售金融资产']
        #
        # df['财务费用正'] = df['减:财务费用'].apply(lambda x: x if x > 0 else 0)
        # df['三费'] = df['减:销售费用'] + df['减:管理费用'] + df['财务费用正']

        df = self.__data_utility.auto_query('', period,
                                            ['减:财务费用', '减:销售费用', '减:管理费用',
                                             '营业总收入', '营业收入', '减:营业成本'],
                                            ['stock_identity', 'period'])

        df['毛利润'] = df['营业收入'] - df['减:营业成本']
        df['财务费用正'] = df['减:财务费用'].apply(lambda x: x if x > 0 else 0)
        df['三费'] = df['减:销售费用'] + df['减:管理费用'] + df['财务费用正']

        s1 = df['三费'] / df['营业总收入']
        s1 = s1.apply(lambda x: (x if x < 1 else 1) if x > -0.1 else -0.1)
        plt.subplot(2, 1, 1)
        s1.hist(bins=100)
        plt.title('三费/营业总收入')

        s2 = df['三费'] / df['毛利润']
        s2 = s2.apply(lambda x: (x if x < 1 else 1) if x > -0.1 else -0.1)
        plt.subplot(2, 1, 2)
        s2.hist(bins=100)
        plt.title('三费/毛利润')

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

        # self.plot_proportion([
        #     ChartLab.PlotItem('固定资产', '资产总计', 0, 1),
        #     ChartLab.PlotItem('息税前利润', '固定资产', -10, 10),
        # ], text_auto_time('2018-12-31'))

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
    sasEntry.get_factor_center()
    return ChartLab(sasEntry.get_data_hub_entry(), sasEntry.get_factor_center()), {'name': '因子图表', 'show': False}


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    app = QApplication(sys.argv)
    wnd = ChartLab(None, None)
    wnd.show()
    sys.exit(app.exec())


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
































