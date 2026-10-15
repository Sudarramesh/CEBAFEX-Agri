"""Currency arithmetic: round each line to paise, decimal ROUND_HALF_UP."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from math import isfinite


def nonnegative_decimal(value):
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError('Money inputs must be finite, numeric and non-negative.') from exc
    if not result.is_finite() or result < 0:
        raise ValueError('Money inputs must be finite, numeric and non-negative.')
    return result


def money(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('Currency result must be finite.')
    with localcontext() as context:
        context.prec = max(28, len(result.as_tuple().digits) + abs(result.as_tuple().exponent) + 5)
        rounded = float(result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    if not isfinite(rounded):
        raise ValueError('Calculated currency exceeds the supported finite range.')
    return rounded


def gross_return(quantity, price):
    return money(nonnegative_decimal(quantity) * nonnegative_decimal(price))


def return_after_transport(quantity, price, transport):
    q, p, cost = map(nonnegative_decimal, (quantity, price, transport))
    return money(Decimal(str(gross_return(q, p))) - Decimal(str(money(cost)))) if q > 0 else 0.0


def sum_money(values):
    return money(sum((Decimal(str(value)) for value in values), Decimal('0')))
