"""Agent 基类：所有角色 Agent 的公共父类"""
from typing import Optional
from src.models.llm_client import LLMClient
from src.harness.context import SharedContext
from src.tools.file_tool import FileTool
from src.tools.command_tool import CommandTool
from src.tools.test_tool import TestTool
from src.tools.git_tool import GitTool


class BaseAgent:
    """Agent 基类，封装通用能力"""

    def __init__(
        self,
        llm: LLMClient,
        context: SharedContext,
        file_tool: FileTool,
        command_tool: CommandTool,
        test_tool: TestTool,
        git_tool: Optional[GitTool] = None,
    ):
        self.llm = llm
        self.context = context
        self.file_tool = file_tool
        self.command_tool = command_tool
        self.test_tool = test_tool
        self.git_tool = git_tool
        self.role = "base"
        self.system_prompt = ""

    def think(self, prompt: str, temperature: float = 0.3) -> str:
        """调用大模型思考，返回结果"""
        result = self.llm.chat(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=temperature,
        )
        # 记录 Token 消耗到上下文
        self.context.total_tokens = self.llm.get_token_usage()
        return result

    def extract_code(self, response: str, language: str = "python") -> str:
        """从模型回复中提取代码块"""
        import re
        # 匹配 ```language ... ``` 格式
        pattern = rf"```{language}\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 如果没有指定语言标记，尝试匹配任意代码块
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 没有代码块，直接返回原文
        return response.strip()

    def log(self, message: str):
        """打印带角色前缀的日志"""
        print(f"[{self.role}] {message}")
