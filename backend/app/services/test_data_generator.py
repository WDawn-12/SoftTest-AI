"""Test Data Generator：测试数据生成器（独立服务）。

根据字段名称自动识别字段类型，并从 JSON 模板（app/data/test_data_templates.json）
生成符合软件测试规范的测试数据（正常/空值/超长/边界/特殊字符/SQL注入/XSS/重复/非法格式）。
"""
import json
import re
from pathlib import Path

from app.models.project import Project
from app.services.crypto_service import decrypt_password

# 类别顺序（软件测试规范要求的 12 类数据，与模板中的 categories 键一致）
CATEGORY_ORDER = [
    "正常",
    "空值",
    "边界值",
    "超长",
    "特殊字符",
    "非法",
    "重复",
    "SQL注入",
    "XSS",
    "中文",
    "英文",
    "数字",
]

TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "data" / "test_data_templates.json"

_templates: dict | None = None


def _load_templates() -> dict:
    """加载模板（带缓存，支持后续扩展字段类型）。"""
    global _templates
    if _templates is None:
        with open(TEMPLATES_PATH, encoding="utf-8") as f:
            _templates = json.load(f)
    return _templates


def _tokens(field: str) -> list[str]:
    """将字段名拆分为词元（兼容 camelCase / snake_case / 中文）。"""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", field)
    parts = re.split(r"[^A-Za-z0-9\u4e00-\u9fff]+", text.lower())
    return [p for p in parts if p]


def detect_type(field: str, type_hint: str | None = None) -> str:
    """识别字段类型：优先显式指定，其次按关键词自动识别，缺省为 string。"""
    templates = _load_templates()
    types = templates.get("types", {})
    if type_hint:
        if type_hint in types:
            return type_hint
        raise ValueError(f"未知字段类型：{type_hint}，可选：{', '.join(types.keys())}")

    tokens = _tokens(field)
    lower_field = field.lower()
    # 归一化字段名（去除下划线/连字符/空格），兼容 id_card、login_name 等写法
    normalized = re.sub(r"[\s_\-]+", "", lower_field)
    for type_key, conf in types.items():
        if type_key == "string":
            continue
        for keyword in conf.get("keywords", []):
            kw = keyword.lower()
            kw_norm = re.sub(r"[\s_\-]+", "", kw)
            # 中文关键词直接包含匹配；英文短词（<6 字符）要求词元精确匹配，避免误判
            if any("\u4e00" <= ch <= "\u9fff" for ch in kw):
                if kw in field:
                    return type_key
            elif kw in tokens:
                return type_key
            elif len(kw_norm) >= 6 and kw_norm in normalized:
                return type_key
    return templates.get("default_type", "string")


def _expand(value: object) -> str:
    """展开模板值：字符串原样返回；{"repeat": ...} 展开重复文本；null 转为空字符串。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "repeat" in value:
        text = str(value["repeat"])
        times = int(value.get("times", 1))
        return text * times
    return str(value)


def generate_test_data(
    field: str, type_hint: str | None = None, count: int = 1
) -> dict:
    """按字段生成测试数据，返回 {field, type, data: [{case, value}, ...]}。"""
    type_key = detect_type(field, type_hint)
    templates = _load_templates()
    conf = templates.get("types", {}).get(type_key, {})
    categories = conf.get("categories", {})
    data: list[dict] = []
    for case in CATEGORY_ORDER:
        values = categories.get(case) or []
        for index in range(count):
            value = values[index % len(values)] if values else None
            data.append({"case": case, "value": _expand(value)})
    return {"field": field, "type": type_key, "data": data}


def detect_fields(text: str) -> list[str]:
    """从测试点文本中识别出现的字段类型（按关键词命中）。"""
    templates = _load_templates()
    found: list[str] = []
    lower_text = text.lower()
    for type_key, conf in templates.get("types", {}).items():
        if type_key == "string":
            continue
        for keyword in conf.get("keywords", []):
            if keyword.lower() in lower_text or keyword in text:
                found.append(type_key)
                break
    return found


def build_test_data_for_point(
    test_point: str, project: Project | None = None
) -> list[dict]:
    """为测试点生成配套测试数据（每类取首条样本），供 TestCase Agent 使用。

    若项目配置了被测系统真实账号密码，则自动注入：
    - 登录场景强制补充「账号 + 密码」字段；
    - 正常数据使用真实账号密码；
    - 额外提供错误账号（账号+123）与错误密码（账号+123）样本。
    """
    templates = _load_templates()
    types = templates.get("types", {})
    login_username = getattr(project, "login_username", None) if project else None
    # 密码在库中为加密存储，需解密后注入测试数据
    login_password = (
        decrypt_password(getattr(project, "login_password", None))
        if project
        else None
    )
    is_login_scene = any(
        keyword in test_point for keyword in ("登录", "登陆", "账号", "密码", "认证")
    )

    result: list[dict] = []
    field_types = detect_fields(test_point) or ["string"]
    # 配置了真实账号且测试点涉及登录/账号/密码时，强制补充账号与密码字段，保证数据完整
    need_credentials = bool(login_username or login_password)
    login_related = is_login_scene or "username" in field_types or "password" in field_types
    if need_credentials and login_related:
        if field_types == ["string"]:
            field_types = ["username", "password"]
        if "username" not in field_types:
            field_types.insert(0, "username")
        if "password" not in field_types:
            field_types.append("password")

    for type_key in field_types:
        conf = types.get(type_key, {})
        categories = conf.get("categories", {})
        samples = {
            case: (_expand(values[0]) if (values := categories.get(case)) else "")
            for case in CATEGORY_ORDER
        }
        # 注入项目真实被测系统账号密码（具体化测试数据）
        if type_key == "username" and login_username:
            samples["正常"] = login_username
            samples["重复"] = login_username
            samples["错误账号"] = f"{login_username}123"
        elif type_key == "password" and login_password:
            samples["正常"] = login_password
            wrong_password = f"{login_username or 'user'}123"
            samples["错误密码"] = wrong_password
            samples["非法"] = wrong_password
        # 展示名称贴合被测系统语境（账号/密码）
        field_name = conf.get("name", type_key)
        if type_key == "username" and login_username and "账号" in test_point:
            field_name = "账号"
        if type_key == "password" and login_password and "密码" in test_point:
            field_name = "密码"
        result.append(
            {
                "field": f"{field_name}（{type_key}）",
                "samples": samples,
            }
        )
    return result
