import functools
import json
import datetime
import pandas as pd


# ----------------------------------------------------------------------------------------------------------------------

# Note that if you import * from common, the datetime importing will be conflict
from StockAnalysisSystem.core.Utiltity.common import ProgressRate


# ----------------------------------------------------------------------------------------------------------------------

"""
Note:
    The object in DataFrame (like time stamp) will be different after serialize and deserialize (it turns to str).
"""

META_PREFIX = '#class:'
DATE_SERIALIZE_FORMAT = '%Y-%m-%d'
DATE_TIME_SERIALIZE_FORMAT = '%Y-%m-%d %H:%M:%S'


SerializeTable = {
    pd.DataFrame:   (lambda py_obj: py_obj.to_dict(orient='records'),
                     lambda json_obj: pd.DataFrame(json_obj)),
    datetime.date:  (lambda py_obj: py_obj.strftime(DATE_SERIALIZE_FORMAT),
                     lambda json_obj: datetime.datetime.strptime(json_obj, DATE_SERIALIZE_FORMAT)),
}


def register_persist_class(cls: object, serialize_func, deserialize_func):
    class_name = cls.__name__
    if class_name not in SerializeTable.keys():
        SerializeTable[class_name] = (serialize_func, deserialize_func)
    else:
        if serialize_func is not None:
            SerializeTable[class_name][0] = serialize_func
        if deserialize_func is not None:
            SerializeTable[class_name][1] = deserialize_func


def JsonSerializer(serialize_class: object):
    def decorator(func):
        register_persist_class(serialize_class, func, None)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def JsonDeserializer(deserialize_class: object):
    def decorator(func):
        register_persist_class(deserialize_class, None, func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ----------------------------------------------------------------------------------------------------------------------

def serialize_obj(py_object: any):
    class_name = py_object.__class__
    if class_name in SerializeTable and SerializeTable[class_name][0] is not None:
        py_serialized = SerializeTable[class_name][0](py_object)
        return {META_PREFIX + class_name: py_serialized}
    else:
        return str(py_object)

    # if isinstance(py_object, pd.DataFrame):
    #     return {'__dataframe__': py_object.to_dict(orient='records')}
    # elif isinstance(py_object, datetime.date):
    #     return {'__date__': py_object.strftime(DATE_SERIALIZE_FORMAT)}
    # elif isinstance(py_object, datetime.datetime):
    #     return {'__datetime__': py_object.strftime(DATE_TIME_SERIALIZE_FORMAT)}
    # elif isinstance(py_object, pd.Timestamp):
    #     return {'__datetime__': py_object.strftime(DATE_TIME_SERIALIZE_FORMAT)}
    # elif isinstance(py_object, ProgressRate):
    #     return {'__progress_rate__': py_object.get_progress_table()}
    # else:
    #     return str(py_object)


def serialize(o: any) -> str:
    return json.dumps(o, default=serialize_obj) if o is not None else ''


# ----------------------------------------------------------------------------------------------------------------------

def deserialize_obj(json_object: dict):
    for key in json_object.keys():
        if key.startswith(META_PREFIX):
            class_name = json_object.__class__
    if class_name in SerializeTable and SerializeTable[class_name][0] is not None:
        py_serialized = SerializeTable[py_object.__class__][0](py_object)
        return py_serialized
    else:
        return json_object

    # if '__dataframe__' in json_object.keys():
    #     df_dict = json_object['__dataframe__']
    #     df_inst = pd.DataFrame(df_dict)
    #     return df_inst
    # if '__date__' in json_object.keys():
    #     date_str = json_object['__date__']
    #     date_inst = datetime.datetime.strptime(date_str, DATE_SERIALIZE_FORMAT)
    #     return date_inst
    # if '__datetime__' in json_object.keys():
    #     datetime_str = json_object['__datetime__']
    #     datetime_inst = datetime.datetime.strptime(datetime_str, DATE_TIME_SERIALIZE_FORMAT)
    #     return datetime_inst
    # if '__progress_rate__' in json_object.keys():
    #     progress_rate_dict = json_object['__progress_rate__']
    #     py_object = ProgressRate()
    #     py_object.set_progress_table(progress_rate_dict)
    #     return py_object
    # else:
    #     return json_object


def deserialize(s: str) -> any:
    return json.loads(s, object_hook=deserialize_obj) if isinstance(s, str) else None

