"""安全工具：密码哈希与 JWT 令牌。"""
from datetime import datetime, timedelta, timezone

import jwt
from bcrypt import checkpw, gensalt, hashpw

from app.core.config import settings
from app.models.user import User


def hash_password(password: str) -> str:
    """生成 bcrypt 密码哈希。"""
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user: User) -> tuple[str, int]:
    """生成 JWT 访问令牌，返回（令牌, 有效期秒数）。"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),  # 用户ID
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, settings.JWT_EXPIRE_MINUTES * 60


def decode_access_token(token: str) -> dict:
    """解析并校验 JWT 令牌，返回载荷；无效或过期时抛出 jwt.PyJWTError。"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
