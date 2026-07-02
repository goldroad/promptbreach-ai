"""
Copyright (c) 2026 八方网域-无涯
"""

import base64
import re
from typing import Optional


def to_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def from_base64(text: str) -> Optional[str]:
    try:
        raw = re.sub(r"\s+", "", text)
        decoded = base64.b64decode(raw, validate=True)
        return decoded.decode("utf-8", errors="ignore")
    except Exception:
        return None


def looks_like_base64(text: str) -> bool:
    if len(text.strip()) < 8:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9+/=\s]+", text.strip()))


def is_non_english(text: str) -> bool:
    return bool(re.search(r"[^\x00-\x7F]", text))


def contains_password_semantics(text: str) -> bool:
    patterns = [
        r"password",
        r"密\s*码",
        r"密\s*钥",
        r"key",
        r"secret",
    ]
    for p in patterns:
        if re.search(p, text, re.I):
            return True
    return False
