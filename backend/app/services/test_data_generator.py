"""Test Data Generator：测试数据生成器（独立服务）。

根据字段名称自动识别字段类型，并从 JSON 模板（app/data/test_data_templates.json）
生成符合软件测试规范的测试数据（正常/空值/超长/边界/特殊字符/SQL注入/XSS/重复/非法格式）。
"""
import json
import re
from pathlib import Path

# 类别顺序（与模板中的 categories 键一致）
CATEGORY_ORDER = [
    "正常",
    "空值",
    "超长",
    "最小值",
    "最大值",
    "特殊字符",
    "SQL注入",
    "XSS",
    "重复数据",
    "非法格式",
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
    for type_key, conf in types.items():
        if type_key == "string":
            continue
        for keyword in conf.get("keywords", []):
            kw = keyword.lower()
            # 中文关键词直接包含匹配；英文短词（<4 字符）要求词元精确匹配，避免误判
            if kw in field or kw in tokens:
                return type_key
            if len(kw) >= 4 and kw in lower_field:
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


def build_test_data_for_point(test_point: str) -> list[dict]:
    """为测试点生成配套测试数据（每类取首条样本），供 TestCase Agent 使用。"""
    templates = _load_templates()
    types = templates.get("types", {})
    result: list[dict] = []
    for type_key in detect_fields(test_point):
        conf = types.get(type_key, {})
        categories = conf.get("categories", {})
        samples = {
            case: (_expand(values[0]) if (values := categories.get(case)) else "")
            for case in CATEGORY_ORDER
        }
        result.append(
            {
                "field": f"{conf.get('name', type_key)}（{type_key}）",
                "samples": samples,
            }
        )
    return result
