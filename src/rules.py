# Business rules that are shared by several tools.

MIN_RECHARGE_AMOUNT = 200   # the platform's lowest allowed recharge, in rupees


def minimum_recharge(shortfall):
    """Smallest recharge that fixes a shortfall: the missing amount, but never below 200."""
    return max(shortfall, MIN_RECHARGE_AMOUNT)