"""Password hashing for staff credentials.

Uses ``bcrypt`` directly rather than the pinned ``passlib[bcrypt]`` wrapper:
passlib 1.7.4 reads ``bcrypt.__about__.__version__`` to pick its backend
handling, and that attribute was removed in bcrypt 4.1, so on the installed
version passlib raises ``AttributeError`` instead of hashing anything.

bcrypt only considers the first 72 bytes of a password, and modern releases
raise rather than truncating. Silently ignoring the rest would make two
different long passwords interchangeable, so the limit is enforced here and
surfaced as a validation error rather than quietly trimmed.
"""

import bcrypt

# bcrypt hashes at most this many bytes; beyond it the remainder is ignored.
MAX_PASSWORD_BYTES = 72


class PasswordTooLong(ValueError):
    pass


def _encode(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise PasswordTooLong(
            f"Password must be at most {MAX_PASSWORD_BYTES} bytes when encoded."
        )
    return encoded


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        candidate = _encode(password)
    except PasswordTooLong:
        # Still spend the comparison, so a caller cannot tell an over-long guess
        # from a wrong one by how long the request took.
        bcrypt.checkpw(b"x" * MAX_PASSWORD_BYTES, password_hash.encode("ascii"))
        return False
    try:
        return bcrypt.checkpw(candidate, password_hash.encode("ascii"))
    except ValueError:
        # A malformed stored hash is a server-side problem, not a wrong password.
        return False
