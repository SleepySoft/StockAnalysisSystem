import sys
import traceback

from .core import *


def main():
    indexer = HistoricalRecordIndexer()
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            indexer.index_path(arg)
    else:
        depot_path = HistoricalRecordLoader.join_local_depot_path('China_CN')
        indexer.index_path(depot_path)
    indexer.dump_to_file('depot/history.index')


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


