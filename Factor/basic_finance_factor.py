
FACTOR_LIST = {
    '67392ca6-f081-41e5-8dde-9530148bf203': ('', ['', '']),
    '77d075b3-fa36-446b-a31e-855ea5d1fdaa': (),
    '0ac83c45-af48-421e-a7ce-8fc128adf799': (),
    '83172ea4-5cd2-4bb2-8703-f66fdba9e58b': (),
    'a518ccd5-525e-4d5f-8e84-1f77bbb8f7af': (),
    'f747c9b1-ed98-4a28-8107-d3fa13d0e5ed': (),
    '6c568b09-3aee-4a6a-8440-542dfc5e8dc5': (),
    'f4d0cc16-afa5-4bf4-a7eb-0a44074634ec': (),
    '308e04df-6bc7-4724-bbc5-168232327ac6': (),
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '',
        'plugin_name': 'DummyFactor',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Sleepy'],
        'factor': FACTOR_LIST,
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return [
        'widget',
    ]


# ----------------------------------------------------------------------------------------------------------------------

