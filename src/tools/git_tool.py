"""Git 操作工具"""
from typing import Optional
from src.tools.command_tool import CommandTool, CommandResult


class GitTool:
    """Git 操作封装，基于 CommandTool"""

    def __init__(self, command_tool: CommandTool):
        self.cmd = command_tool

    def init(self) -> CommandResult:
        """初始化 git 仓库"""
        return self.cmd.run("git init")

    def add(self, path: str = ".") -> CommandResult:
        """git add"""
        return self.cmd.run(f"git add {path}")

    def commit(self, message: str) -> CommandResult:
        """git commit"""
        safe_message = message.replace('"', '\\"')
        return self.cmd.run(f'git commit -m "{safe_message}"')

    def status(self) -> CommandResult:
        """git status"""
        return self.cmd.run("git status --short")

    def diff(self, path: Optional[str] = None) -> CommandResult:
        """git diff"""
        cmd = "git diff"
        if path:
            cmd += f" {path}"
        return self.cmd.run(cmd)

    def log(self, count: int = 10) -> CommandResult:
        """git log"""
        return self.cmd.run(f"git log --oneline -{count}")

    def branch(self) -> CommandResult:
        """查看分支"""
        return self.cmd.run("git branch")

    def checkout(self, branch: str) -> CommandResult:
        """切换分支"""
        return self.cmd.run(f"git checkout {branch}")
