"""命令执行工具"""
import subprocess
from typing import Optional
from pydantic import BaseModel
from src.config import COMMAND_TIMEOUT


class CommandResult(BaseModel):
    """命令执行结果"""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timeout: bool = False


class CommandTool:
    """命令执行工具，限制在工作目录内运行"""

    def __init__(self, workspace_dir: str, timeout: int = COMMAND_TIMEOUT):
        self.workspace_dir = workspace_dir
        self.timeout = timeout

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """执行 shell 命令

        Args:
            command: 要执行的命令
            cwd: 工作目录（相对于 workspace），默认 workspace 根目录
            timeout: 超时时间（秒），默认使用全局配置
        """
        work_dir = self.workspace_dir
        if cwd:
            from pathlib import Path
            work_dir = str((Path(self.workspace_dir) / cwd).resolve())

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
            )
            return CommandResult(
                command=command,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"命令超时（{timeout or self.timeout}秒）",
                timeout=True,
            )
        except Exception as e:
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"执行异常: {str(e)}",
            )
