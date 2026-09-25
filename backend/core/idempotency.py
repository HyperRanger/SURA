from typing import Dict, Optional

_IDEMPOTENCY_KEYS: Dict[str, str] = {}


def record_idempotency_key(key: str, result: str) -> None:
    _IDEMPOTENCY_KEYS[key] = result


def get_idempotency_result(key: str) -> Optional[str]:
    return _IDEMPOTENCY_KEYS.get(key)
