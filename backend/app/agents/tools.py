"""Agent 工具注册表：把业务能力暴露给大模型（OpenAI function calling）。

工具 schema 采用 OpenAI 函数调用格式；执行器 run_tool 根据名称分发到具体服务。
"""
import json

from sqlalchemy.orm import Session

# 工具定义（OpenAI function calling JSON Schema）
TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "generate_test_data",
            "description": (
                "按字段名称生成覆盖 12 类软件测试场景的测试数据"
                "（正常/空值/边界值/超长/特殊字符/非法/重复/SQL注入/XSS/中文/英文/数字）。"
                "当用户询问某个字段的测试数据时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "字段名称，如：用户名、密码、手机号、邮箱、金额",
                    },
                    "type": {
                        "type": "string",
                        "description": "字段类型（可选，缺省自动识别，如 string/integer/email/phone）",
                    },
                    "count": {
                        "type": "integer",
                        "description": "每个类别生成的数据条数（1-10，默认 1）",
                    },
                },
                "required": ["field"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_knowledge",
            "description": (
                "获取当前项目知识库：需求文档解析结果、测试用例、被测系统信息。"
                "当用户询问项目需求/用例/功能模块等知识库相关内容时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# 工具名称集合（校验用）
TOOL_NAMES = {schema["function"]["name"] for schema in TOOL_SCHEMAS}


def run_tool(
    name: str,
    args: dict | None,
    db: Session | None = None,
    project_id: int | None = None,
) -> dict:
    """执行工具，返回 JSON 可序列化结果。"""
    args = args or {}
    if name == "generate_test_data":
        from app.services.test_data_generator import generate_test_data

        field = str(args.get("field", "")).strip()
        if not field:
            raise ValueError("generate_test_data 缺少 field 参数")
        return generate_test_data(
            field=field,
            type_hint=args.get("type"),
            count=int(args.get("count", 1)),
        )

    if name == "get_project_knowledge":
        from app.services.chat_service import build_project_knowledge

        if db is None or project_id is None:
            raise ValueError("get_project_knowledge 需要项目上下文")
        return {"knowledge": build_project_knowledge(db, project_id)}

    raise ValueError(f"未知工具：{name}")


def summarize_tool_result(result: dict, max_len: int = 2000) -> str:
    """把工具结果序列化为字符串（作为 ToolMessage 内容喂回模型）。"""
    text = json.dumps(result, ensure_ascii=False)
    if len(text) > max_len:
        text = text[:max_len] + "…（已截断）"
    return text
