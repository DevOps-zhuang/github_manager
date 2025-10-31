from __future__ import annotations

from datetime import date, datetime
import re
from typing import Tuple

_PHONE_PATTERN = re.compile(r"^1\d{10}$")
_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_CHECK_CODES = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]
_MIN_AGE = 18


def _age_from_birth(birth: date) -> int:
    today = date.today()
    years = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        years -= 1
    return years


def is_valid_phone(phone: str) -> bool:
    ok, _ = validate_phone(phone)
    return ok


def validate_phone(phone: str) -> Tuple[bool, str]:
    normalized = (phone or "").strip()
    if not normalized:
        return False, "手机号不能为空"
    if not _PHONE_PATTERN.fullmatch(normalized):
        return False, "手机号格式不正确"
    return True, ""


def is_valid_id_card(id_card: str) -> bool:
    ok, _ = validate_id_card(id_card)
    return ok


def validate_id_card(id_card: str) -> Tuple[bool, str]:
    normalized = (id_card or "").strip().upper()
    if len(normalized) != 18 or not normalized[:17].isdigit() or normalized[-1] not in "0123456789X":
        return False, "身份证号格式或校验码不正确"

    birth_str = normalized[6:14]
    try:
        birth = datetime.strptime(birth_str, "%Y%m%d").date()
    except ValueError:
        return False, "身份证号中包含无效日期"

    if _age_from_birth(birth) < _MIN_AGE:
        return False, "身份证号对应年龄未满18周岁"

    checksum = sum(int(d) * w for d, w in zip(normalized[:17], _WEIGHTS))
    if _CHECK_CODES[checksum % 11] != normalized[-1]:
        return False, "身份证号格式或校验码不正确"

    return True, ""
