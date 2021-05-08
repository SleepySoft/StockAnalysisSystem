import datetime
import traceback
import collections
import pandas as pd

from .JsonSerializer import *

# ----------------------------------------------------------------------------------------------------------------------

# Import custom class here

# Note that if you import * from common, the datetime importing will be conflict
from StockAnalysisSystem.core.Utility.common import ProgressRate

# ----------------------------------------------------------------------------------------------------------------------


register_persist_class(pd.DataFrame,        lambda py_obj: py_obj.to_dict(orient='records'),
                                            lambda json_obj: pd.DataFrame(json_obj))
register_persist_class(datetime.date,       lambda py_obj: py_obj.strftime(DATE_SERIALIZE_FORMAT),
                                            lambda json_obj: datetime.datetime.strptime(json_obj, DATE_SERIALIZE_FORMAT).date())
register_persist_class(datetime.datetime,   lambda py_obj: py_obj.strftime(DATE_TIME_SERIALIZE_FORMAT),
                                            lambda json_obj: datetime.datetime.strptime(json_obj, DATE_TIME_SERIALIZE_FORMAT))
register_persist_class(pd.Timestamp,        lambda py_obj: py_obj.strftime(DATE_TIME_SERIALIZE_FORMAT),
                                            lambda json_obj: datetime.datetime.strptime(json_obj, DATE_TIME_SERIALIZE_FORMAT))


@JsonSerializer(ProgressRate)
def serialize_progress_rate(py_obj):
    return dict(py_obj.get_progress_table())


@JsonDeserializer(ProgressRate)
def serialize_progress_rate(json_obj: dict):
    py_object = ProgressRate()
    py_object.set_progress_table(collections.OrderedDict(sorted(json_obj.items())))
    return py_object


# ----------------------------------------------------------------------------------------------------------------------


def main():
    print('OK')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass






