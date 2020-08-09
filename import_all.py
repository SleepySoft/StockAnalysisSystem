# To ensure the pyInstaller patches all the modules and dependencies

import sys
import time
import logging
import pyqtgraph
import traceback
import matplotlib
import tushare as ts

import StockAnalysisSystem.core.Utiltity.AnalyzerUtility
import StockAnalysisSystem.core.Utiltity.CollectorUtility
import StockAnalysisSystem.core.Utiltity.common
import StockAnalysisSystem.core.Utiltity.constant
import StockAnalysisSystem.core.Utiltity.dependency
import StockAnalysisSystem.core.Utiltity.df_utility
import StockAnalysisSystem.core.Utiltity.digit_utility
import StockAnalysisSystem.core.Utiltity.FactorUtility
import StockAnalysisSystem.core.Utiltity.plugin_manager
import StockAnalysisSystem.core.Utiltity.securities_selector
import StockAnalysisSystem.core.Utiltity.TableViewEx
import StockAnalysisSystem.core.Utiltity.task_queue
import StockAnalysisSystem.core.Utiltity.time_utility
import StockAnalysisSystem.core.Utiltity.ui_utility

# NOTE: If plugin depends on any lib, please import here. Otherwise the packing program cannot find this lib.
# 注意：如果插件依赖于任何库，请务必在这里导入（让打包工具知道有这个依赖项），否则打包后运行可能找不到该库



