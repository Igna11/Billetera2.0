"""
Billeterapp 2.0 - Junio 2024
Billeterapp 2.0 - v2.0 Marzo 2026

This module handles password hashing and verification. It uses the following structure to make the hash:
- algorithm$iterations$salt$hash
"""

import os
import hmac
import hashlib
import binascii

ALGORITHM = "pbkdf2_sha512"
ITERATIONS = 720000
SALT_SIZE = 60


class UnauthorizedError(Exception):
    pass


def hash_password(password: str) -> str:
    """
    Hash a password for storing in db using PBKDF2 algorithm

    Args:
        password (str): The password to hash in plain text.

    Returns:
        str: The hashed password.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    salt = hashlib.sha256(os.urandom(SALT_SIZE)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, ITERATIONS)
    pwdhash = binascii.hexlify(pwdhash)
    pwd = "$".join([ALGORITHM, str(ITERATIONS), salt.decode("ascii"), pwdhash.decode("ascii")])
    return pwd


def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a stored password against one provided by user

    Args:
        stored_password (str): The stored password (hashed).
        provided_password (str): The password provided by user (plain text).

    Returns:
        bool: True if the password match, False otherwise.
    """
    try:
        algorithm, iterations, salt, stored_hash = stored_password.split("$")
    except ValueError:
        return False

    if algorithm != ALGORITHM:
        return False

    pwdhash_bytes = hashlib.pbkdf2_hmac(
        "sha512", provided_password.encode("utf-8"), salt.encode("ascii"), int(iterations)
    )
    pwdhash_str = binascii.hexlify(pwdhash_bytes).decode("ascii")
    return hmac.compare_digest(pwdhash_str, stored_hash)
