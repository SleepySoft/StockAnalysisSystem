import re
import sys
import traceback

CN_NUM = {
    '0': 0,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,

    '〇': 0,
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,

    '零': 0,
    '壹': 1,
    '贰': 2,
    '叁': 3,
    '肆': 4,
    '伍': 5,
    '陆': 6,
    '柒': 7,
    '捌': 8,
    '玖': 9,

    '貮': 2,
    '两': 2,
}
CN_UNIT_L1 = {
    '十': 10,
    '拾': 10,
    '百': 100,
    '佰': 100,
    '千': 1000,
    '仟': 1000,
}
CN_UNIT_L2 = {
    '万': 10000,
    '萬': 10000,
    '亿': 100000000,
    '億': 100000000,
    '兆': 1000000000000,
}


def cn_num_to_digit(cn_num: str):
    """
    Algorithm:
        a.  The best way is parse from lower digit to upper digit.
        b.  The Chinese number has 2 level of unit:
                L1: 十百千; L2: 万亿兆...
            For L1 unit, it cannot be decorated. For L2 unit, it can be decorated by the unit that less than itself.
                Example: 一千万 is OK, but 一百千 or 一亿万 is invalid.
                More complex Example: 五万四千三百二十一万亿 四千三百二十一万 四千三百二十一
            We can figured out that:
                1. The L1 unit should not composite. 四千三百二十一 -> 4 * 1000 + 3 * 100 + 2 * 10 + 1
                2. The L2 unit should be composted. If we meet 万, the base unit should multiple with 10000.
                3. If we meet a larger L2 unit. The base unit should reset to it.
    :param cn_num: A single cn number string.
    :return: The digit that comes from cn number.
    """
    sum_num = 0
    unit_l1 = 1
    unit_l2 = 1
    unit_l2_max = 0
    digit_missing = False
    num_chars = list(cn_num)

    while num_chars:
        num_char = num_chars.pop()
        if num_char in CN_UNIT_L1:
            unit_l1 = CN_UNIT_L1.get(num_char)
            digit_missing = True
        elif num_char in CN_UNIT_L2:
            unit = CN_UNIT_L2.get(num_char)
            if unit > unit_l2_max:
                unit_l2_max = unit
                unit_l2 = unit
            else:
                unit_l2 *= unit
            unit_l1 = 1
            digit_missing = True
        elif num_char in CN_NUM:
            digit = CN_NUM.get(num_char) * unit_l1 * unit_l2
            # For discrete digit. It has no effect to the standard expression.
            unit_l1 *= 10
            sum_num += digit
            digit_missing = False
        else:
            continue
    if digit_missing:
        sum_num += unit_l1 * unit_l2

    print(cn_num + ' -> ' + str(sum_num))
    return sum_num


pattern = re.compile(r'([0123456789〇一二三四五六七八九零壹贰叁肆伍陆柒捌玖貮两十拾百佰千仟万萬亿億兆]+)')


def text_cn_num_to_arab(text: str) -> str:
    match_text = pattern.findall(text)
    match_text = list(set(match_text))
    match_text.sort(key=lambda x: len(x), reverse=True)
    for cn_num in match_text:
        text = text.replace(cn_num, str(cn_num_to_digit(cn_num)))
    return text


# ----------------------------------------------------- Test Code ------------------------------------------------------

def test_cn_time_to_digit():
    assert cn_num_to_digit('零') == 0
    assert cn_num_to_digit('一') == 1
    assert cn_num_to_digit('二') == 2
    assert cn_num_to_digit('两') == 2
    assert cn_num_to_digit('三') == 3
    assert cn_num_to_digit('四') == 4
    assert cn_num_to_digit('五') == 5
    assert cn_num_to_digit('六') == 6
    assert cn_num_to_digit('七') == 7
    assert cn_num_to_digit('八') == 8
    assert cn_num_to_digit('九') == 9

    assert cn_num_to_digit('十') == 10
    assert cn_num_to_digit('百') == 100
    assert cn_num_to_digit('千') == 1000
    assert cn_num_to_digit('万') == 10000
    assert cn_num_to_digit('亿') == 100000000

    assert cn_num_to_digit('一十') == 10
    assert cn_num_to_digit('一百') == 100
    assert cn_num_to_digit('一千') == 1000
    assert cn_num_to_digit('一万') == 10000
    assert cn_num_to_digit('一亿') == 100000000

    assert cn_num_to_digit('二十') == 20
    assert cn_num_to_digit('两百') == 200
    assert cn_num_to_digit('五千') == 5000
    assert cn_num_to_digit('八万') == 80000
    assert cn_num_to_digit('九亿') == 900000000

    assert cn_num_to_digit('十亿') == 1000000000
    assert cn_num_to_digit('百亿') == 10000000000
    assert cn_num_to_digit('千亿') == 100000000000
    assert cn_num_to_digit('万亿') == 1000000000000
    assert cn_num_to_digit('十万亿') == 10000000000000
    assert cn_num_to_digit('百万亿') == 100000000000000
    assert cn_num_to_digit('千万亿') == 1000000000000000
    assert cn_num_to_digit('万万亿') == 10000000000000000
    assert cn_num_to_digit('亿亿') == 10000000000000000

    assert cn_num_to_digit('一千一百一十一亿一千一百一十一万一千一百一十一') == 111111111111
    assert cn_num_to_digit('九千八百七十六亿五千四百三十二万一千两百三十四') == 987654321234
    assert cn_num_to_digit('五万四千三百二十一万亿四千三百二十一万四千三百二十一') == 54321000043214321
    assert cn_num_to_digit('九千八百七十六万一千二百三十四亿五千四百三十二万一千两百三十四') == 9876123454321234

    print(text_cn_num_to_arab('''
    基本数字有：一，二或两，三，四及五，六，七和八，以及九共十个数字
    支持的位数包括：最简单的十，大一点的百，还有千，更大的万和最终的亿共五个进位
    先来点简单的：
        一万
        二千
        三百
        八亿
    以及由此组合成的复杂数字：
        其中有五十二个
        或者是一百七十三只
        试我们试试两百零六怎样
        那么三千五百七十九呢
        一千两百二十亿零两万零五十肯定有问题
        再看看这个数字一千五百三十六万零四十
        这个够复杂了吧一万八千亿三千六百五十万零七十九
    以及离散数字
       二九九七九二四五八
       三点一四一五九二六
    '''))


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_cn_time_to_digit()
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















