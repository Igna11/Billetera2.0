"""
Billeterapp 2.0 - Junio 2024

This module handles password hashing and verification. It uses the following structure to make the hash:
- algorithm$iterations$salt$hash
"""

import os
import hashlib
import binascii


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
    algorithm = "pbkdf2_sha512"
    iterations = 720000
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iterations)
    pwdhash = binascii.hexlify(pwdhash)
    pwd = "$".join([algorithm, str(iterations), salt.decode("ascii"), pwdhash.decode("ascii")])
    return pwd


def is_hash(password: str) -> bool:
    """
    Returns True if the password provided is a hash, False otherwise.

    Args:
        password (str): The password to check.

    Returns:
        bool: True if the password provided is a hash, False otherwise.
    """
    return password.startswith("pbkdf2_sha512") and len(password) == 214


def verify_password(stored_password: str, provided_password) -> bool:
    """
    Verify a stored password against one provided by user

    Args:
        stored_password (str): The stored password (hashed).
        provided_password (str): The password provided by user (plain text).

    Returns:
        bool: True if the password match, False otherwise.
    """
    salt = stored_password[21:85]
    stored_password = stored_password[86:]
    pwdhash = hashlib.pbkdf2_hmac("sha512", provided_password.encode("utf-8"), salt.encode("ascii"), 720000)
    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
    return pwdhash == stored_password
