import logging
import os
import time
import traceback

from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.log import logging_config, logging_test


# ----------------------------------------------------------------------------------------------------------------------

def init_sas(work_path: str, config: Config or None) -> bool:
    try:
        print('Init StockAnalysisSystem...')
        from StockAnalysisSystem.interface.interface_local import LocalInterface
        __sas_interface = LocalInterface()
        __sas_interface.if_init(project_path=work_path, config=config)
        print('Init StockAnalysisSystem Complete.')
        return True
    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        print('Init StockAnalysisSystem Fail')
        return False
    finally:
        pass


def main():
    logging_config()
    logging_test()

    if not init_sas(os.getcwd(), None):
        exit(1)

    while True:
        # TODO: Add something?
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass
