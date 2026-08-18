"""系统设置服务：模型配置、API Key、Prompt 模板（数据库优先，环境变量兜底）。"""
from sqlalchemy.orm import Session

from app.agents.chat_agent import SYSTEM_PROMPT as CHAT_SYSTEM_PROMPT
from app.agents.requirement_agent import SYSTEM_PROMPT as REQUIREMENT_SYSTEM_PROMPT
from app.agents.testcase_agent import SYSTEM_PROMPT as TESTCASE_SYSTEM_PROMPT
from app.agents.testpoint_agent import SYSTEM_PROMPT as TESTPOINT_SYSTEM_PROMPT
from app.agents.interface_testcase_agent import SYSTEM_PROMPT as INTERFACE_TESTCASE_SYSTEM_PROMPT
from app.core.config import settings
from app.models.system_setting import SystemSetting

# 默认设置（未入库或未配置时回退；Prompt 模板默认使用内置提示词）
DEFAULT_SETTINGS: dict[str, str] = {
    "ai_provider": settings.AI_PROVIDER,
    "openai_api_key": settings.OPENAI_API_KEY,
    "openai_base_url": settings.OPENAI_BASE_URL,
    "openai_model": settings.OPENAI_MODEL,
    "deepseek_api_key": settings.DEEPSEEK_API_KEY,
    "deepseek_base_url": settings.DEEPSEEK_BASE_URL,
    "deepseek_model": settings.DEEPSEEK_MODEL,
    "prompt_requirement": REQUIREMENT_SYSTEM_PROMPT,
    "prompt_testpoint": TESTPOINT_SYSTEM_PROMPT,
    "prompt_testcase": TESTCASE_SYSTEM_PROMPT,
    "prompt_interface_testcase": INTERFACE_TESTCASE_SYSTEM_PROMPT,
    "prompt_chat": CHAT_SYSTEM_PROMPT,
}


def get_setting(db: Session, key: str) -> str:
    """读取单个设置：数据库优先，未配置时返回默认值。"""
    row = (
        db.query(SystemSetting)
        .filter(SystemSetting.setting_key == key)
        .first()
    )
    if row and row.setting_value is not None:
        return row.setting_value
    return DEFAULT_SETTINGS.get(key, "")


def get_all_settings(db: Session) -> dict[str, str]:
    """读取全部设置（默认值 + 数据库覆盖）。"""
    result = dict(DEFAULT_SETTINGS)
    for row in db.query(SystemSetting).all():
        result[row.setting_key] = row.setting_value or ""
    return result


def update_settings(db: Session, values: dict[str, str]) -> dict[str, str]:
    """批量更新设置（仅允许白名单内的键）。"""
    for key, value in values.items():
        if key not in DEFAULT_SETTINGS:
            continue
        row = (
            db.query(SystemSetting)
            .filter(SystemSetting.setting_key == key)
            .first()
        )
        if row:
            row.setting_value = str(value)
        else:
            db.add(
                SystemSetting(
                    setting_key=key,
                    setting_value=str(value),
                    description=key,
                )
            )
    db.commit()
    return get_all_settings(db)
