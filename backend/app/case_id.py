from __future__ import annotations

import secrets
import string

CASE_ID_PREFIX = "ATLAS-CASE"
CASE_ID_ALPHABET = string.ascii_uppercase + string.digits


def generate_case_id() -> str:
    suffix = "".join(secrets.choice(CASE_ID_ALPHABET) for _ in range(6))
    return f"{CASE_ID_PREFIX}-{suffix}"
