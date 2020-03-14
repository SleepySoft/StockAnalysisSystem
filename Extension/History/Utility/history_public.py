import math
import sys
import traceback


# ----------------------------------------------------- Functions ------------------------------------------------------

def str_to_int(text: str, default: int=0):
    try:
        return int(text)
    except Exception as e:
        return default
    finally:
        pass


def str_includes(text: str, includes: [str]) -> bool:
    for sub_str in includes:
        if sub_str in text:
            return True
    return False


def list_unique(list1: list) -> list:
    return list(set(list1))


def list_union_unique(list1: list, list2: list) -> list:
    return list(set(list1).union(set(list2)))


def compare_intersection(list1, list2) -> bool:
    return len(list(set(list1).intersection(set(list2)))) > 0


def check_normalize_expects(expects: list) -> list or None:
    """
    Make expects as a list.
    :param expects: The parameter that need to be normalized
    :return: None if the expects is invalid.
    """
    if expects is None:
        return None
    if isinstance(expects, (list, tuple)):
        if len(expects) == 0:
            return None
        return expects
    else:
        return [expects]


def check_condition_range(conditions: dict, key: str, expects: list) -> bool:
    expects = check_normalize_expects(expects)
    if expects is None:
        return True
    value = conditions.get(key, None)
    if value is None:
        return True
    lower = min(expects)
    upper = max(expects)
    if isinstance(value, (list, tuple)):
        for v in value:
            if v < lower or v > upper:
                return False
        return True
    else:
        return lower < value < upper


def check_condition_within(conditions: dict, key: str, expects: list) -> bool:
    expects = check_normalize_expects(expects)
    if expects is None:
        return True
    value = conditions.get(key, None)
    if value is None:
        return True
    if not isinstance(value, (list, tuple)):
        return value in expects
    else:
        return compare_intersection(value, expects)


def upper_rough(num):
    abs_num = abs(num)
    index_10 = math.log(abs_num, 10)
    round_index_10 = math.floor(index_10)
    scale = math.pow(10, round_index_10)
    if num >= 0:
        integer = math.ceil(abs_num / scale)
    else:
        integer = math.floor(abs_num / scale)
    rough = integer * scale
    result = rough if num >= 0 else -rough
    return result


def lower_rough(num):
    abs_num = abs(num)
    if abs_num == 0:
        return 0
    index_10 = math.log(abs_num, 10)
    round_index_10 = math.floor(index_10)
    scale = math.pow(10, round_index_10)
    if num >= 0:
        integer = math.floor(abs_num / scale)
    else:
        integer = math.ceil(abs_num / scale)
    rough = integer * scale
    result = rough if num >= 0 else -rough
    return result


def scale_round(num: float, scale: float):
    return (round(num / scale) + 1) * scale


# ----------------------------------------------------- Test Code ------------------------------------------------------

def test_upper_rough():
    assert math.isclose(upper_rough(10001), 20000)
    assert math.isclose(upper_rough(10000), 10000)
    assert math.isclose(upper_rough(9999), 10000)
    assert math.isclose(upper_rough(9001), 10000)
    assert math.isclose(upper_rough(8999),  9000)
    assert math.isclose(upper_rough(1.1), 2)
    # assert math.isclose(upper_rough(0.07), 0.07)

    assert math.isclose(upper_rough(-10001), -10000)
    assert math.isclose(upper_rough(-10000), -10000)
    assert math.isclose(upper_rough(-9999), -9000)
    assert math.isclose(upper_rough(-9001), -9000)
    assert math.isclose(upper_rough(-8999), -8000)
    assert math.isclose(upper_rough(-1.1), -1.0)
    # assert math.isclose(upper_rough(-0.07), 0.07)


def test_lower_rough():
    assert math.isclose(lower_rough(10001), 10000)
    assert math.isclose(lower_rough(10000), 10000)
    assert math.isclose(lower_rough(9999), 9000)
    assert math.isclose(lower_rough(9001), 9000)
    assert math.isclose(lower_rough(8999),  8000)
    assert math.isclose(lower_rough(1.1), 1.0)
    # assert math.isclose(lower_rough(0.07), 0.07)

    assert math.isclose(lower_rough(-10001), -20000)
    assert math.isclose(lower_rough(-10000), -10000)
    assert math.isclose(lower_rough(-9999), -10000)
    assert math.isclose(lower_rough(-9001), -10000)
    assert math.isclose(lower_rough(-8999), -9000)
    assert math.isclose(lower_rough(-1.1), -2.0)
    # assert math.isclose(upper_rough(-0.07), 0.07)


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_upper_rough()
    test_lower_rough()
    print('All test passed.')


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




