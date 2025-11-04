from __future__ import annotations

import logging
from typing import Tuple

from .validators import validate_id_card, validate_phone

_LOGGER_NAME = "auth.validation.failure"


def get_failure_logger() -> logging.Logger:
    """Return the shared logger for user validation failures."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def validate_user(phone: str, id_card: str) -> bool:
    phone_ok, phone_reason = validate_phone(phone)
    id_ok, id_reason = validate_id_card(id_card)

    if phone_ok or id_ok:
        return True

    logger = get_failure_logger()
    logger.error("验证失败：手机号[%s]；身份证[%s]", phone_reason or "未知原因", id_reason or "未知原因")
    return False
