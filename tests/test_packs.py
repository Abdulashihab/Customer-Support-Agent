from src.tools.account import get_account
from src.tools.packs import add_pack, drop_pack


# ---------- add_pack ----------

def test_add_pack_updates_packs_and_monthly_charge(db_copy):
    # 100003 pays 512 and has balance 850. Adding Telugu Kids (219) makes it 731.
    result = add_pack("100003", "DSK-TLK1", db_path=db_copy)
    assert result["ok"] is True
    assert result["new_monthly_charge"] == 731
    account = get_account("100003", db_path=db_copy)
    assert account["monthly_charge"] == 731
    assert "DSK-TLK1" in [p["pack_id"] for p in account["packs"]]


def test_add_pack_reports_overlapping_channels(db_copy):
    # Tamil Kids SD shares only channel 319 (Chutti TV) with Tamil Kids HD
    result = add_pack("100003", "DSK-TMK1", db_path=db_copy)
    assert result["ok"] is True
    assert result["overlapping_channels"] == [319]


def test_add_pack_already_subscribed(db_copy):
    result = add_pack("100003", "DSK-TMK2", db_path=db_copy)
    assert result == {"ok": False, "reason": "already_subscribed"}


def test_add_pack_unknown_pack(db_copy):
    result = add_pack("100003", "DSK-NOPE", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_pack"}


def test_add_pack_unknown_subscriber(db_copy):
    result = add_pack("999999", "DSK-TLK1", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_subscriber"}


def test_add_pack_to_suspended_connection(db_copy):
    result = add_pack("100005", "DSK-TLK1", db_path=db_copy)
    assert result == {"ok": False, "reason": "connection_suspended"}


def test_add_pack_needs_enough_balance(db_copy):
    # 100013 has balance 300 and pays 153. Adding a 219 pack needs 372, so 72 is missing.
    # The minimum recharge is 200, so the customer must recharge at least 200.
    result = add_pack("100013", "DSK-TMK1", db_path=db_copy)
    assert result == {
        "ok": False,
        "reason": "insufficient_balance",
        "required": 372,
        "balance": 300,
        "shortfall": 72,
        "minimum_recharge": 200,
    }


# ---------- drop_pack ----------

def test_drop_pack_updates_packs_and_monthly_charge(db_copy):
    result = drop_pack("100003", "DSK-TMK2", db_path=db_copy)
    assert result["ok"] is True
    assert result["new_monthly_charge"] == 153          # only the base pack is left
    assert len(result["channels_lost"]) == 10           # all 10 channels of the pack
    assert result["channels_kept"] == []
    account = get_account("100003", db_path=db_copy)
    assert [p["pack_id"] for p in account["packs"]] == ["DSK-BASIC"]


def test_drop_pack_keeps_channels_that_other_packs_still_give(db_copy):
    # 100012 has News+Sports HD and Kids+Cinema HD, which share 4 channels
    result = drop_pack("100012", "DSK-MK2", db_path=db_copy)
    assert result["ok"] is True
    assert result["new_monthly_charge"] == 821          # 1180 - 359
    assert result["channels_kept"] == [201, 205, 206, 207]
    assert result["channels_lost"] == [202, 216, 603, 605, 608, 609]


def test_base_pack_cannot_be_dropped(db_copy):
    result = drop_pack("100003", "DSK-BASIC", db_path=db_copy)
    assert result == {"ok": False, "reason": "base_pack_cannot_be_dropped"}


def test_drop_pack_not_subscribed(db_copy):
    result = drop_pack("100003", "DSK-MNS1", db_path=db_copy)
    assert result == {"ok": False, "reason": "pack_not_subscribed"}


def test_drop_pack_unknown_subscriber(db_copy):
    result = drop_pack("999999", "DSK-TMK2", db_path=db_copy)
    assert result == {"ok": False, "reason": "unknown_subscriber"}


def test_drop_pack_from_suspended_connection(db_copy):
    result = drop_pack("100005", "DSK-KNNS2", db_path=db_copy)
    assert result == {"ok": False, "reason": "connection_suspended"}