from __future__ import annotations

from datetime import date, timedelta
import logging
from pathlib import Path
from typing import Tuple

import pytest

from auth.service import get_failure_logger, validate_user
from auth.validators import (
    is_valid_id_card,
    is_valid_phone,
    validate_id_card,
    validate_phone,
)


def _date_for_age(years: int, *, adjust_days: int = 0) -> date:
    today = date.today()
    target_year = today.year - years
    day = today.day
    month = today.month
    while True:
        try:
            base = date(target_year, month, day)
            break
        except ValueError:
            day -= 1
    return base + timedelta(days=adjust_days)


def _generate_id_number(birth_date: date, sequence: int = 1) -> str:
    prefix = "110105"
    seq_part = f"{sequence:03d}"
    base = f"{prefix}{birth_date:%Y%m%d}{seq_part}"
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    codes = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]
    total = sum(int(digit) * weight for digit, weight in zip(base, weights))
    return f"{base}{codes[total % 11]}"


def test_is_valid_phone_accepts_legit_number() -> None:
    assert is_valid_phone("13800138000")


def test_is_valid_phone_rejects_invalid_number() -> None:
    assert not is_valid_phone("123456")


def test_validate_phone_returns_reason() -> None:
    ok, reason = validate_phone(" ")
    assert not ok
    assert "手机号" in reason


def test_is_valid_id_card_accepts_adult() -> None:
    birth = _date_for_age(20)
    id_card = _generate_id_number(birth)
    assert is_valid_id_card(id_card)


def test_is_valid_id_card_rejects_underage() -> None:
    birth = _date_for_age(17)
    id_card = _generate_id_number(birth)
    assert not is_valid_id_card(id_card)


def test_validate_id_card_detects_bad_checksum() -> None:
    birth = _date_for_age(20)
    valid = _generate_id_number(birth)
    bad_checksum = valid[:-1] + ("0" if valid[-1] != "0" else "1")
    ok, reason = validate_id_card(bad_checksum)
    assert not ok
    assert "格式或校验码" in reason


def test_validate_id_card_detects_invalid_date() -> None:
    invalid_id = "11010519900230001X"
    ok, reason = validate_id_card(invalid_id)
    assert not ok
    assert "身份证号" in reason


def test_validate_user_succeeds_when_phone_valid() -> None:
    assert validate_user("13900000000", "invalid")


def test_validate_user_succeeds_when_id_valid() -> None:
    birth = _date_for_age(25)
    id_card = _generate_id_number(birth)
    assert validate_user("invalid", id_card)


def test_validate_user_logs_failure(tmp_path: Path) -> None:
    logger = get_failure_logger()
    original_handlers = list(logger.handlers)
    for handler in original_handlers:
        logger.removeHandler(handler)

    log_file = tmp_path / "failure.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    try:
        assert not validate_user("123", "abc")
    finally:
        logger.removeHandler(handler)
        handler.close()
        for original in original_handlers:
            logger.addHandler(original)

    contents = log_file.read_text(encoding="utf-8")
    assert "验证失败" in contents
    assert "手机号" in contents
    assert "身份证" in contents
