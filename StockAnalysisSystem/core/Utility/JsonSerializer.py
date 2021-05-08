import json

"""
***** When you import this file. You should also import JsonSerializerImpl.py for serializer/deserializer register *****
    
Note:

    The object in DataFrame (like time stamp) will be different after serialize and deserialize (it turns to str).
    Except you implement customer serialize/deserialize function and register to the SerializeTable.

    We usually register our customer serialize/deserialize function in JsonSerializerImpl.py
"""

META_PREFIX = '#class:'
DATE_SERIALIZE_FORMAT = '%Y-%m-%d'
DATE_TIME_SERIALIZE_FORMAT = '%Y-%m-%d %H:%M:%S'


SerializeTable = {
    # Class name: [serialize function, deserialize function],
}


# ----------------------------------------------------------------------------------------------------------------------

def register_persist_class(cls: object, serialize_func, deserialize_func):
    class_name = cls.__name__
    if class_name not in SerializeTable.keys():
        SerializeTable[class_name] = [serialize_func, deserialize_func]
    else:
        if serialize_func is not None:
            SerializeTable[class_name][0] = serialize_func
        if deserialize_func is not None:
            SerializeTable[class_name][1] = deserialize_func


def JsonSerializer(serialize_class: object):
    def decorator(func):
        register_persist_class(serialize_class, func, None)
        return func
    return decorator


def JsonDeserializer(deserialize_class: object):
    def decorator(func):
        register_persist_class(deserialize_class, None, func)
        return func
    return decorator


# ----------------------------------------------------------------------------------------------------------------------

def serialize_obj(py_object: any):
    class_type = py_object.__class__
    class_name = class_type.__name__
    if class_name in SerializeTable and SerializeTable[class_name][0] is not None:
        py_serialized = SerializeTable[class_name][0](py_object)
        return {META_PREFIX + class_name: py_serialized}
    else:
        return str(py_object)


def serialize(o: any) -> str:
    return json.dumps(o, default=serialize_obj) if o is not None else ''


# ----------------------------------------------------------------------------------------------------------------------

def deserialize_obj(json_object: dict):
    try:
        for key in json_object.keys():
            if key.startswith(META_PREFIX):
                class_name = key[len(META_PREFIX):]
                if class_name in SerializeTable.keys():
                    class_data = json_object[key]
                    return SerializeTable[class_name][1](class_data)
    except Exception as e:
        pass
    finally:
        pass
    return json_object


def deserialize(s: str) -> any:
    return json.loads(s, object_hook=deserialize_obj) if isinstance(s, str) else None


