

def can_ignore_or_negative(value: float, reference: float, tolerance: float = 0.1) -> bool:
    return value < 0.0 or (abs(value) / reference < tolerance)


def can_ignore_or_positive(value: float, reference: float, tolerance: float = 0.1) -> bool:
    return value > 0.0 or (abs(value) / reference < tolerance)


def format_f(value: float, precision) -> str:
    formatter = '%%.0%sf' % precision
    return formatter % value


def format_pct(value: float, precision: int = 2) -> str:
    return format_f(value * 100, precision) + '%'


def format_w(value: float, precision: int = 2) -> str:
    return format_f(value / 10000, precision) + '万'




