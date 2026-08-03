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
        # 演示供应商：按任务类型返回对应示例（测试点 / 测试用例 / 需求解析）
        functions = self._extract_functions(user_prompt)
        if functions is not None:
            return json.dumps(
                {"test_points": self._generate_testpoints(functions)},
                ensure_ascii=False,
            )
        test_points = self._extract_testpoints(user_prompt)
        if test_points is not None:
            return json.dumps(
                {"test_cases": self._generate_testcases(test_points)},
                ensure_ascii=False,
            )
        if "对话内容：" in user_prompt:
            return self._chat_demo(user_prompt)
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

    def _extract_testpoints(self, user_prompt: str) -> list[dict] | None:
        """从用户提示中提取测试点 JSON（TestCase Agent 专用）。"""
        fence = re.search(r"```json\s*(.*?)```", user_prompt, re.S)
        if not fence:
            return None
        try:
            data = json.loads(fence.group(1))
        except json.JSONDecodeError:
            return None
        if (
            isinstance(data, list)
            and data
            and "name" in data[0]
            and "category" in data[0]
        ):
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

    def _generate_testcases(self, test_points: list[dict]) -> list[dict]:
        """按五类测试点生成演示测试用例。"""
        cases: list[dict] = []
        for point in test_points:
            name = str(point.get("name", "功能测试"))
            category = str(point.get("category", "normal"))
            module = str(point.get("module", "核心模块"))
            # 从「xxx」中提取功能名作为 title
            match = re.search(r"「([^」]+)」", name)
            title = match.group(1) if match else module
            priority = "高" if category == "security" else "中"
            expected = {
                "normal": "操作成功，结果符合预期",
                "exception": "系统给出明确错误提示，流程不中断",
                "boundary": "边界值处理正确，无越界或异常",
                "security": "未授权/恶意操作被拒绝，数据安全",
                "compatibility": "各浏览器/分辨率下表现一致",
            }.get(category, "操作成功")
            cases.append(
                {
                    "module": module,
                    "title": title,
                    "test_point": name,
                    "test_data": {
                        "normal": "有效账号与正确输入数据",
                        "exception": "非法字符、错误格式、异常操作等数据",
                        "boundary": "最小/最大长度、空值、临界值等数据",
                        "security": "越权访问、注入、弱口令等攻击数据",
                        "compatibility": "不同浏览器/分辨率/设备环境数据",
                    }.get(category, "有效输入数据"),
                    "priority": priority,
                    "preconditions": "系统运行正常，当前用户具备相应操作权限",
                    "steps": [
                        f"进入「{title}」对应功能页面",
                        "输入测试数据并执行操作",
                        "观察并记录系统反馈",
                    ],
                    "expected_result": expected,
                    "remark": "由 TestCase Agent 生成，可人工编辑",
                }
            )
        return cases

    def _chat_demo(self, user_prompt: str) -> str:
        """聊天任务的演示输出（Markdown）。"""
        marker = "对话内容："
        idx = user_prompt.find(marker)
        question = user_prompt[idx + len(marker) :].strip() or "（空问题）"
        has_knowledge = "项目知识库：" in user_prompt and "（暂无内容）" not in user_prompt
        lines = [
            "### 演示模式回复",
            "",
            f"**您的问题**：{question}",
            "",
            "当前为**演示模式**（未配置 OpenAI / DeepSeek API Key），以下为基于项目知识库的示例回答。",
            "",
        ]
        if has_knowledge:
            lines.append(
                "> 项目知识库已包含需求文档与测试用例，配置 API Key 后可获得真实的智能问答。"
            )
        else:
            lines.append("> 当前项目知识库暂无内容，请先上传需求文档并生成测试点/测试用例。")
        return "\n".join(lines)


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
