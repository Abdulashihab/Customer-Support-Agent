from src.rules import minimum_recharge


def test_small_shortfall_still_needs_the_minimum_recharge():
    assert minimum_recharge(72) == 200


def test_big_shortfall_needs_the_full_missing_amount():
    assert minimum_recharge(1500) == 1500