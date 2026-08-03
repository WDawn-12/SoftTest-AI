"""大模型调用层：OpenAI / DeepSeek（OpenAI 兼容协议）与本地演示模式。"""
import json
import re
from abc import ABC, abstractmethod

from app.core.config import settings


class LLMProvider(ABC):
    """大模型供应商抽象接口。"""

    name: str = "base"

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """发送对话请求，返回模型回复文本。"""
        raise NotImplementedError


class OpenAILikeProvider(LLMProvider):
    """OpenAI 兼容协议供应商（OpenAI / DeepSeek 共用同一套实现）。"""

    def __init__(self, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=0.2,
            timeout=120,
        )
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        return str(response.content).strip()


class DemoProvider(LLMProvider):
    """演示供应商：未配置 API Key 时使用，返回固定结构的示例解析结果。"""

    name = "demo"

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        # 演示供应商：优先按「测试点生成」任务生成示例，否则返回需求解析示例
        functions = self._extract_functions(user_prompt)
        if functions is not None:
            return json.dumps(
                {"test_points": self._generate_testpoints(functions)},
                ensure_ascii=False,
            )
        return self._requirement_demo(user_prompt)

    def _extract_functions(self, user_prompt: str) -> list[dict] | None:
        """从用户提示中提取功能点 JSON（TestPoint Agent 专用）。"""
        fence = re.search(r"```json\s*(.*?)```", user_prompt, re.S)
        if not fence:
            return None
        try:
            data = json.loads(fence.group(1))
        except json.JSONDecodeError:
            return None
        if isinstance(data, list) and data and "functions" in data[0]:
            return data
        return None

    def _generate_testpoints(self, functions: list[dict]) -> list[dict]:
        """按五类测试规则生成演示测试点。"""
        points: list[dict] = []
        for module in functions:
            module_name = module.get("module", "核心模块")
            for fn in module.get("functions", []):
                points.extend(
                    [
                        {
                            "category": "normal",
                            "module": module_name,
                            "name": f"验证「{fn}」功能正常可用",
                        },
                        {
                            "category": "exception",
                            "module": module_name,
                            "name": f"验证「{fn}」在非法输入或异常操作时给出正确提示",
                        },
                        {
                            "category": "boundary",
                            "module": module_name,
                            "name": f"验证「{fn}」输入边界值（最小/最大/空值）的处理",
                        },
                        {
                            "category": "security",
                            "module": module_name,
                            "name": f"验证「{fn}」的权限控制与安全防护",
                        },
                        {
                            "category": "compatibility",
                            "module": module_name,
                            "name": f"验证「{fn}」在主流浏览器/分辨率下兼容运行",
                        },
                    ]
                )
        if not points:
            points.append(
                {"category": "normal", "module": "核心模块", "name": "验证核心功能正常可用"}
            )
        return points

    def _requirement_demo(self, user_prompt: str) -> str:
        """需求解析任务的演示输出。"""
        content = user_prompt.strip()
        marker = "需求文档内容：\n"
        idx = content.find(marker)
        body = content[idx + len(marker) :] if idx != -1 else content
        preview = (body[:60] + "…") if len(body) > 60 else (body or "（无文本内容）")
        return json.dumps(
            {
                "summary": f"需求概述：{preview}",
                "modules": [
                    {
                        "name": "用户管理",
                        "description": "用户注册、登录与权限管理",
                        "functions": ["用户注册", "用户登录", "权限控制"],
                    },
                    {
                        "name": "核心业务",
                        "description": "系统核心业务功能",
                        "functions": ["业务数据录入", "业务查询与统计"],
                    },
                    {
                        "name": "系统管理",
                        "description": "系统配置与运维",
                        "functions": ["系统参数配置", "操作日志管理"],
                    },
                ],
                "roles": ["管理员", "普通用户"],
                "business_flows": [
                    {
                        "name": "用户登录流程",
                        "steps": ["打开系统登录页", "输入账号密码", "系统校验凭证", "进入主界面"],
                    },
                    {
                        "name": "业务数据维护流程",
                        "steps": ["进入业务模块", "新增或编辑数据", "保存并校验", "生成记录"],
                    },
                ],
                "risks": [
                    {
                        "type": "安全风险",
                        "description": "用户凭证可能被暴力破解，应限制登录失败次数并启用验证码",
                        "level": "高",
                    },
                    {
                        "type": "数据一致性",
                        "description": "并发操作可能导致数据不一致，需引入事务与行级锁",
                        "level": "中",
                    },
                    {
                        "type": "可用性",
                        "description": "高并发访问可能导致服务不可用，需进行性能压测与限流",
                        "level": "中",
                    },
                ],
            },
            ensure_ascii=False,
        )


def get_llm_provider() -> LLMProvider:
    """根据配置创建大模型供应商实例（openai / deepseek / demo）。"""
    provider = settings.AI_PROVIDER.strip().lower()
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("未配置 OPENAI_API_KEY，请在系统设置或 .env 中配置")
        return OpenAILikeProvider(
            "openai", settings.OPENAI_API_KEY, settings.OPENAI_BASE_URL, settings.OPENAI_MODEL
        )
    if provider == "deepseek":
        if not settings.DEEPSEEK_API_KEY:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请在系统设置或 .env 中配置")
        return OpenAILikeProvider(
            "deepseek", settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_BASE_URL, settings.DEEPSEEK_MODEL
        )
    return DemoProvider()
