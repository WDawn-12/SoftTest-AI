"""大模型调用层：OpenAI / DeepSeek（OpenAI 兼容协议）与本地演示模式。"""
import json
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
        # 仅用于未接入真实大模型的演示环境；生产环境请配置 OpenAI / DeepSeek 密钥
        content = user_prompt.strip()
        # 截取「需求文档内容」之后的正文作为概述预览
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
