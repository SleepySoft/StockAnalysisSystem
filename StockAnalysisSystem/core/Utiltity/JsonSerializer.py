import json
import datetime
import pandas as pd


# ----------------------------------------------------------------------------------------------------------------------

"""
Note:
    The object in DataFrame (like time stamp) will be different after serialize and deserialize (it turns to str).
"""


# ----------------------------------------------------------------------------------------------------------------------

def serialize_obj(py_object: any):
    if isinstance(py_object, pd.DataFrame):
        return {'__dataframe__': py_object.to_dict(orient='records')}
    elif isinstance(py_object, pd.Timestamp):
        return py_object.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(py_object, datetime.date):
        return py_object.strftime('%Y-%m-%d')
    elif isinstance(py_object, datetime.datetime):
        return py_object.strftime('%Y-%m-%d %H:%M:%S')
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
    else:
        return json_object


def deserialize(s: str) -> any:
    return json.loads(s, object_hook=deserialize_obj) if isinstance(s, str) else None

