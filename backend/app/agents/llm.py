"""大模型调用层：OpenAI / DeepSeek（OpenAI 兼容协议）与本地演示模式。"""
import json
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator

from sqlalchemy.orm import Session

from app.core.config import settings


def _chunk_text(text: str, size: int = 16) -> Iterator[str]:
    """按固定长度切分文本为若干块（模拟流式输出）。"""
    for i in range(0, len(text), size):
        yield text[i : i + size]


class LLMProvider(ABC):
    """大模型供应商抽象接口。"""

    name: str = "base"

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """发送对话请求，返回模型回复文本。"""
        raise NotImplementedError

    def stream_chat(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """流式发送对话请求，逐块产出回复文本。

        默认实现：调用 chat() 获取完整回复后分块产出；
        子类（如 OpenAI 兼容协议）可覆盖为真正的逐 token 流式。
        """
        content = self.chat(system_prompt, user_prompt)
        yield from _chunk_text(content)

    def run_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        tool_handler: Callable[[str, dict], dict],
    ) -> tuple[list[dict], str | None]:
        """执行工具调用阶段。

        返回 (工具调用记录, 最终回复文本)；未命中任何工具时返回 ([], None)，
        调用方应继续走普通对话流程。

        默认实现：不调用任何工具。
        """
        return [], None


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

    def stream_chat(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """使用 OpenAI 兼容接口的流式模式逐 token 产出回复。"""
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=0.2,
            timeout=120,
            streaming=True,
        )
        for chunk in llm.stream(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        ):
            piece = getattr(chunk, "content", "")
            if piece:
                yield str(piece)

    def run_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        tool_handler: Callable[[str, dict], dict],
    ) -> tuple[list[dict], str | None]:
        """OpenAI 函数调用循环：让模型自主决策调用工具，直到给出最终回复。"""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
        from langchain_openai import ChatOpenAI

        from app.agents.tools import summarize_tool_result

        llm = ChatOpenAI(
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=0.2,
            timeout=120,
        ).bind_tools(tools)

        messages: list = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        records: list[dict] = []
        for _round in range(5):  # 最多 5 轮工具调用，防止死循环
            ai_msg = llm.invoke(messages)
            messages.append(ai_msg)
            tool_calls = getattr(ai_msg, "tool_calls", None)
            if not tool_calls:
                return records, str(ai_msg.content or "").strip()
            for tc in tool_calls:
                name = tc.get("name", "")
                args = tc.get("args") or {}
                try:
                    result = tool_handler(name, args)
                except Exception as exc:  # 工具执行失败也回传模型，由其决定后续
                    result = {"error": str(exc)}
                records.append({"name": name, "args": args, "result": result})
                messages.append(
                    ToolMessage(
                        content=summarize_tool_result(result),
                        tool_call_id=tc.get("id", ""),
                    )
                )
        # 达到轮次上限：返回最后一段回复
        return records, str(messages[-1].content or "").strip()


class DemoProvider(LLMProvider):
    """演示供应商：未配置 API Key 时使用，返回固定结构的示例解析结果。"""

    name = "demo"

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        # 演示供应商：按任务类型返回对应示例（测试点 / 测试用例 / 接口用例 / 需求解析）
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
        interfaces = self._extract_interfaces(user_prompt)
        if interfaces is not None:
            return json.dumps(
                {"test_cases": self._generate_interface_cases(interfaces)},
                ensure_ascii=False,
            )
        if "对话内容：" in user_prompt:
            return self._chat_demo(user_prompt)
        return self._requirement_demo(user_prompt)

    def stream_chat(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """演示供应商流式输出：完整回复按块产出，块间小延迟模拟打字机效果。"""
        content = self.chat(system_prompt, user_prompt)
        for piece in _chunk_text(content, size=8):
            yield piece
            time.sleep(0.01)

    def run_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        tool_handler: Callable[[str, dict], dict],
    ) -> tuple[list[dict], str | None]:
        """演示供应商工具模拟：按关键词识别工具意图并执行真实工具。

        demo 模式下大模型不参与决策，用关键词匹配模拟 Agent 的工具调用行为。
        """
        # 生成测试数据：问题提到字段 + 测试数据
        field = self._detect_field(user_prompt)
        if field:
            result = tool_handler("generate_test_data", {"field": field})
            records = [{"name": "generate_test_data", "args": {"field": field}, "result": result}]
            lines = [
                f"已调用工具 **generate_test_data**（字段：{field}，共 {len(result.get('data', []))} 类）",
                "",
                "| 类别 | 测试数据 |",
                "| --- | --- |",
            ]
            for item in result.get("data", []):
                lines.append(f"| {item.get('case', '')} | {item.get('value', '')} |")
            lines.extend(
                [
                    "",
                    "> 当前为演示模式（关键词模拟工具调用）；配置真实 API Key 后，"
                    "大模型将自主决策调用哪些工具。",
                ]
            )
            return records, "\n".join(lines)
        return [], None

    # 常见字段名关键词（用于 demo 模式工具识别）
    _FIELD_KEYWORDS = ["用户名", "账号", "密码", "手机号", "手机号码", "邮箱", "姓名", "身份证", "金额", "库存", "地址"]

    def _detect_field(self, user_prompt: str) -> str | None:
        """从用户问题中识别字段名；未命中返回 None。"""
        if not any(kw in user_prompt for kw in ("测试数据", "生成数据", "数据样本", "造数据")):
            return None
        for keyword in self._FIELD_KEYWORDS:
            if keyword in user_prompt:
                return keyword
        # 兜底：匹配「xxx」内的字段名
        match = re.search(r"「([^」]{1,20})」", user_prompt)
        return match.group(1) if match else None

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

    def _extract_interfaces(self, user_prompt: str) -> list[dict] | None:
        """从用户提示中提取接口定义 JSON（InterfaceTestCase Agent 专用）。"""
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
            and "path" in data[0]
            and "method" in data[0]
        ):
            return data
        return None

    def _generate_interface_cases(self, interfaces: list[dict]) -> list[dict]:
        """按五类规则生成演示接口测试用例。"""
        cases: list[dict] = []
        no = 0
        for api in interfaces:
            iface_id = api.get("id")
            method = str(api.get("method", "GET")).upper()
            path = str(api.get("path", "/"))
            name = str(api.get("name") or path)
            summary = str(api.get("summary") or "") or name
            # 解析路径中的 {占位符}，生成实际取值（demo 用 1 占位）
            placeholders = re.findall(r"\{(\w+)\}", path)
            path_with_value = path
            for ph in placeholders:
                path_with_value = path_with_value.replace(f"{{{ph}}}", "1")
            categories = [
                ("normal", "验证「{0}」接口正常调用返回预期结果", "200", "高", "请求合法，接口返回预期数据"),
                ("exception", "验证「{0}」接口缺失必填参数时返回错误", "400/422", "中", "接口返回明确错误信息，不抛 500"),
                ("boundary", "验证「{0}」接口参数边界值（空值/超长/极值）的处理", "400/200", "中", "边界值处理正确，无越界或异常"),
                ("security", "验证「{0}」接口鉴权缺失与注入攻击防护", "401/403/400", "高", "未授权请求被拒绝，注入被拦截"),
                ("parameter", "验证「{0}」接口参数组合与格式兼容性", "200/400", "中", "合法组合成功，非法组合给出提示"),
            ]
            for category, template, status, priority, expected in categories:
                no += 1
                title = template.format(name)
                cases.append(
                    {
                        "interface_id": iface_id,
                        "title": title,
                        "category": category,
                        "method": method,
                        "path": path_with_value or path,
                        "test_data": "username=test_user, page=1, page_size=10",
                        "request_payload": self._demo_payload(method),
                        "expected_status": status,
                        "expected_result": expected,
                        "priority": priority,
                        "preconditions": "接口服务运行正常，网络连通",
                        "steps": [
                            f"构造 {method} 请求 {path}",
                            f"按 {category} 场景设置参数并发送请求",
                            "检查响应状态码与返回体是否符合预期",
                        ],
                        "remark": f"由 InterfaceTestCase Agent 生成（{category} 场景）",
                    }
                )
        return cases

    @staticmethod
    def _demo_payload(method: str) -> str:
        """demo 模式的示例请求体。"""
        if method in ("GET", "DELETE"):
            return "?username=test_user&page=1&page_size=10"
        return json.dumps(
            {"username": "test_user", "password": "123456"}, ensure_ascii=False
        )

    def _generate_testpoints(self, functions: list[dict]) -> list[dict]:
        """按六类测试规则生成演示测试点。"""
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
                        {
                            "category": "performance",
                            "module": module_name,
                            "name": f"验证「{fn}」的响应时间、并发处理与资源占用",
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
                    "test_data": self._pick_test_data(point.get("test_data"), name),
                    "priority": priority,
                    "preconditions": "系统运行正常，当前用户具备相应操作权限",
                    "steps": [
                        f"进入「{title}」对应功能页面",
                        "输入测试数据并执行操作",
                        "观察并记录系统反馈",
                    ],
                    "expected_result": expected,
                    "remark": "由 TestCase Agent 生成，测试数据来自 Test Data Generator",
                }
            )
        return cases

    def _pick_test_data(self, test_data: object, point_name: str) -> str:
        """从生成器输出的样本中按测试点场景选取完整测试数据。"""
        if not isinstance(test_data, list) or not test_data:
            # 兜底：使用字符串类型样本（正常服务流程不会触发）
            from app.services.test_data_generator import build_test_data_for_point

            test_data = build_test_data_for_point(point_name)
        if not test_data:
            return ""
        lower_name = point_name.lower()
        is_wrong = any(
            keyword in point_name
            for keyword in ("错误", "失败", "不正确", "无效", "wrong")
        )
        is_empty = "为空" in point_name or "空值" in point_name
        is_boundary = any(
            keyword in point_name for keyword in ("边界", "最小", "最大")
        )
        is_overlong = "超长" in point_name
        is_sql = "注入" in lower_name or "sql" in lower_name
        is_xss = "xss" in lower_name
        is_invalid_format = "非法" in point_name or "格式" in point_name
        is_special = "特殊" in point_name
        is_repeat = "重复" in point_name
        is_chinese = "中文" in point_name
        is_english = "英文" in point_name or "english" in lower_name
        is_number = "数字" in point_name or "数值" in point_name

        lines = []
        for item in test_data:
            samples = item.get("samples") if isinstance(item, dict) else {}
            if not isinstance(samples, dict):
                continue
            field = item.get("field", "")
            is_password_field = "password" in field
            is_username_field = "username" in field
            mentioned_username = "用户名" in point_name or "账号" in point_name
            mentioned_password = "密码" in point_name

            def pick(case_key: str) -> str:
                """按类别键取值；缺失时回退正常值（空字符串是合法取值，不能回退）。"""
                if case_key in samples:
                    return samples[case_key]
                return samples.get("正常", "")

            if is_empty:
                # 空值只作用于测试点描述中提到的字段，其余字段保持正常值
                if is_username_field and ("用户名" in point_name or "账号" in point_name):
                    value = pick("空值")
                elif is_password_field and "密码" in point_name:
                    value = pick("空值")
                else:
                    value = pick("正常")
            elif is_boundary:
                value = (
                    pick("边界值")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_overlong:
                value = (
                    pick("超长")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_sql:
                value = pick("SQL注入")
            elif is_xss:
                value = pick("XSS")
            elif is_invalid_format:
                value = (
                    pick("非法")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_special:
                value = (
                    pick("特殊字符")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_repeat:
                value = (
                    pick("重复")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_chinese:
                value = (
                    pick("中文")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_english:
                value = (
                    pick("英文")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_number:
                value = (
                    pick("数字")
                    if (mentioned_username if is_username_field else mentioned_password if is_password_field else True)
                    else pick("正常")
                )
            elif is_wrong:
                # 密码错误：账号用正常值、密码用错误密码；账号错误：反之
                pwd_wrong = any(
                    keyword in point_name
                    for keyword in ("密码错误", "密码不正确", "密码无效", "密码失败")
                )
                acc_wrong = any(
                    keyword in point_name
                    for keyword in ("账号错误", "用户名错误", "账号不正确", "用户名不正确")
                )
                if is_password_field:
                    if "错误密码" in samples and (pwd_wrong or not acc_wrong):
                        value = samples["错误密码"]
                    else:
                        value = pick("正常")
                elif is_username_field:
                    value = (
                        pick("错误账号")
                        if ("错误账号" in samples and acc_wrong)
                        else pick("正常")
                    )
                else:
                    value = pick("正常")
            else:
                value = pick("正常")
            # 空值按规范示例显示为 ""
            display = '""' if value == "" else value
            lines.append(f"{item.get('field', '字段')}：{display}")
        return "\n".join(lines)

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


def get_llm_provider(db: Session | None = None) -> LLMProvider:
    """创建大模型供应商实例；传入 db 时优先使用系统设置（数据库）中的配置。"""
    if db is not None:
        from app.services.system_settings_service import get_setting

        provider = get_setting(db, "ai_provider").strip().lower()
        openai_key = get_setting(db, "openai_api_key")
        openai_base_url = get_setting(db, "openai_base_url")
        openai_model = get_setting(db, "openai_model")
        deepseek_key = get_setting(db, "deepseek_api_key")
        deepseek_base_url = get_setting(db, "deepseek_base_url")
        deepseek_model = get_setting(db, "deepseek_model")
    else:
        provider = settings.AI_PROVIDER.strip().lower()
        openai_key = settings.OPENAI_API_KEY
        openai_base_url = settings.OPENAI_BASE_URL
        openai_model = settings.OPENAI_MODEL
        deepseek_key = settings.DEEPSEEK_API_KEY
        deepseek_base_url = settings.DEEPSEEK_BASE_URL
        deepseek_model = settings.DEEPSEEK_MODEL

    if provider == "openai":
        if not openai_key:
            raise ValueError("未配置 OPENAI_API_KEY，请在系统设置或 .env 中配置")
        return OpenAILikeProvider(
            "openai", openai_key, openai_base_url, openai_model
        )
    if provider == "deepseek":
        if not deepseek_key:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请在系统设置或 .env 中配置")
        return OpenAILikeProvider(
            "deepseek", deepseek_key, deepseek_base_url, deepseek_model
        )
    return DemoProvider()
