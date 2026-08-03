"""敏感信息加密服务：使用 Fernet 对称加密（测试密码等）。"""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_key() -> bytes:
    """获取加密密钥：优先 FERNET_KEY，未配置时由 SECRET_KEY 派生。"""
    if settings.FERNET_KEY:
        return settings.FERNET_KEY.encode("utf-8")
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_password(plain_password: str | None) -> str | None:
    """加密明文密码。"""
    if not plain_password:
        return None
    return Fernet(_get_key()).encrypt(plain_password.encode("utf-8")).decode("utf-8")


def decrypt_password(encrypted: str | None) -> str | None:
    """解密密码；解密失败返回 None。"""
    if not encrypted:
        return None
    try:
        return Fernet(_get_key()).decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except Exception:
        return None
