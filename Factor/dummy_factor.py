
FACTOR_LIST = {
    # uuid: (factor name, depends fields, factor comments, factor calc entry, reserve1, reserve2, reserve3)
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'cc43c66a-dabd-45a8-9698-b32e1817536d',
        'plugin_name': 'DummyFactor',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Factor', 'Sleepy'],
        'factor': FACTOR_LIST,
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return [
        'widget',
    ]


# ----------------------------------------------------------------------------------------------------------------------















