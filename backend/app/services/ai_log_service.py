"""AI 调用日志服务。"""
from sqlalchemy.orm import Session

from app.models.ai_call_log import AiCallLog


def log_ai_call(
    db: Session,
    *,
    user_id: int | None,
    agent: str,
    provider: str | None,
    prompt_length: int,
    response_length: int,
    duration_ms: int,
    status: str = "success",
    error_message: str | None = None,
) -> None:
    """记录一次 AI 调用日志。"""
    db.add(
        AiCallLog(
            user_id=user_id,
            agent=agent,
            provider=provider,
            prompt_length=prompt_length,
            response_length=response_length,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
        )
    )
    db.commit()
