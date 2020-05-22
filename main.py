import os
import sys
import traceback

import import_all
import StockAnalysisSystem.api as sas_api


def main():
    project_path = os.path.dirname(os.path.abspath(__file__))
    sas_api.sas().check_initialize(project_path)
    sas_api.run_ui()
    print('Process Quit.')


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
