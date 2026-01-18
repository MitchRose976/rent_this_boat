"""Password hashing and verification utilities using Argon2."""

from passlib.context import CryptContext
import os


def _get_password_context() -> CryptContext:
    """
    Create and return a CryptContext configured from passlib.cfg file.

    Configuration is loaded from (in order of priority):
    1. passlib.cfg in the same directory as this file
    2. PASSLIB_CONFIG_PATH environment variable (path to config file)
    3. PASSLIB_CONFIG environment variable (INI format string)
    4. Default hardcoded config

    Returns:
        CryptContext configured for password hashing
    """
    # Try to load from passlib.cfg in the same directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_config_path = os.path.join(current_dir, "passlib.cfg")
    if os.path.exists(local_config_path):
        return CryptContext.from_path(local_config_path)

    # Try to load from config file path
    config_path = os.getenv("PASSLIB_CONFIG_PATH")
    if config_path:
        return CryptContext.from_path(config_path)

    # Try to load from config string
    config_string = os.getenv("PASSLIB_CONFIG")
    if config_string:
        return CryptContext.from_string(config_string)

    # Fallback to default config
    # OWASP recommended settings for Argon2
    default_config = """
    [passlib]
    schemes = argon2
    deprecated =
    argon2__memory_cost = 65536
    argon2__time_cost = 3
    argon2__parallelism = 4
    """
    return CryptContext.from_string(default_config)


# Initialize the password context once at module load
pwd_context = _get_password_context()


def hash_password(password: str) -> str:
    """
    Hash a plain text password.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string (safe to store in database)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
