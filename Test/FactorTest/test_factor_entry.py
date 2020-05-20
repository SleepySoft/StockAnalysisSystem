import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import traceback
from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

from StockAnalysisSystem.core.FactorEntry import FactorCenter
from StockAnalysisSystem.core.Utiltity.plugin_manager import PluginManager


# ----------------------------------------------------- Test Code ------------------------------------------------------

def __build_factor_center() -> FactorCenter:
    plugin = PluginManager(path.join(root_path, 'plugin', 'Factor'))
    factor = FactorCenter(None, None, plugin)
    return factor


def test_basic():
    factor = __build_factor_center()
    factor.reload_plugin()


def test_entry():
    test_basic()


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_entry()

    # If program reaches here, all test passed.
    print('All test passed.')


# ------------------------------------------------- Exception Handling -------------------------------------------------

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


# def factor_test_entry(sas: StockAnalysisSystem):
#     test_most_useful_factor.test_entry(sas)
#
#
# # ----------------------------------------------------------------------------------------------------------------------
#
# def main():
#     sas = StockAnalysisSystem()
#     assert sas.check_initialize()
#
#     factor_test_entry(sas)
#
#     print('Process Quit.')
#
#
# # ----------------------------------------------------------------------------------------------------------------------
#
# def exception_hook(type, value, tback):
#     # log the exception here
#     print('Exception hook triggered.')
#     print(type)
#     print(value)
#     print(tback)
#     # then call the default handler
#     sys.__excepthook__(type, value, tback)
#
#
# if __name__ == "__main__":
#     sys.excepthook = exception_hook
#     try:
#         main()
#     except Exception as e:
#         print('Error =>', e)
#         print('Error =>', traceback.format_exc())
#         exit()
#     finally:
#         pass






