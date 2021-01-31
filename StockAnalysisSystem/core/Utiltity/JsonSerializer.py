import json
import datetime
import pandas as pd

# Note that if you import * from common, the datetime importing will be conflict
from StockAnalysisSystem.core.Utiltity.common import ProgressRate


# ----------------------------------------------------------------------------------------------------------------------

"""
Note:
    The object in DataFrame (like time stamp) will be different after serialize and deserialize (it turns to str).
"""

DATE_SERIALIZE_FORMAT = '%Y-%m-%d'
DATE_TIME_SERIALIZE_FORMAT = '%Y-%m-%d %H:%M:%S'


# ----------------------------------------------------------------------------------------------------------------------

def serialize_obj(py_object: any):
    if isinstance(py_object, pd.DataFrame):
        return {'__dataframe__': py_object.to_dict(orient='records')}
    elif isinstance(py_object, datetime.date):
        return {'__date__': py_object.strftime(DATE_SERIALIZE_FORMAT)}
    elif isinstance(py_object, datetime.datetime):
        return {'__datetime__': py_object.strftime(DATE_TIME_SERIALIZE_FORMAT)}
    elif isinstance(py_object, pd.Timestamp):
        return {'__datetime__': py_object.strftime(DATE_TIME_SERIALIZE_FORMAT)}
    elif isinstance(py_object, ProgressRate):
        return {'__progress_rate__': py_object.get_progress_table()}
    else:
        return str(py_object)


def serialize(o: any) -> str:
    return json.dumps(o, default=serialize_obj) if o is not None else ''


# ----------------------------------------------------------------------------------------------------------------------

def deserialize_obj(json_object: dict):
    if '__dataframe__' in json_object.keys():
        df_dict = json_object['__dataframe__']
        df_inst = pd.DataFrame(df_dict)
        return df_inst
    if '__date__' in json_object.keys():
        date_str = json_object['__date__']
        date_inst = datetime.datetime.strptime(date_str, DATE_SERIALIZE_FORMAT)
        return date_inst
    if '__datetime__' in json_object.keys():
        datetime_str = json_object['__datetime__']
        datetime_inst = datetime.datetime.strptime(datetime_str, DATE_TIME_SERIALIZE_FORMAT)
        return datetime_inst
    if '__progress_rate__' in json_object.keys():
        progress_rate_dict = json_object['__progress_rate__']
        py_object = ProgressRate()
        py_object.set_progress_table(progress_rate_dict)
        return py_object
    else:
        return json_object


def deserialize(s: str) -> any:
    return json.loads(s, object_hook=deserialize_obj) if isinstance(s, str) else None

