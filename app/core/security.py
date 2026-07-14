from cryptography.fernet import Fernet

from app.core.config import settings

_fernet = Fernet(settings.SECRET_KEY.encode())


def encrypt_password(plain_password: str) -> str:
    """
    Encrypts a target-database password before it's persisted to
    `database_connections.password`. Never store `plain_password` directly.
    """
    return _fernet.encrypt(plain_password.encode()).decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypts a password read back from `database_connections.password`.
    Call this at the point a target-DB connection URL is built — never log
    or return the decrypted value.
    """
    return _fernet.decrypt(encrypted_password.encode()).decode()
