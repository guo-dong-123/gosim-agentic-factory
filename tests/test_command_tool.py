"""CommandTool 单元测试"""
import pytest
import tempfile
import shutil
from src.tools.command_tool import CommandTool


@pytest.fixture
def workspace():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def command_tool(workspace):
    return CommandTool(workspace, timeout=10)


class TestCommandTool:
    def test_run_echo(self, command_tool):
        """测试执行 echo 命令"""
        result = command_tool.run("echo hello")
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_run_with_error(self, command_tool):
        """测试执行失败的命令"""
        result = command_tool.run("ls /nonexistent_dir_12345")
        assert result.exit_code != 0
        assert result.stderr != ""

    def test_timeout(self, command_tool):
        """测试命令超时"""
        result = command_tool.run("sleep 5", timeout=1)
        assert result.timeout is True
        assert result.exit_code == -1

    def test_cwd(self, command_tool, workspace):
        """测试指定工作目录"""
        import os
        os.makedirs(os.path.join(workspace, "subdir"), exist_ok=True)
        result = command_tool.run("pwd", cwd="subdir")
        assert result.exit_code == 0
        assert "subdir" in result.stdout

    def test_complex_command(self, command_tool):
        """测试复杂命令"""
        result = command_tool.run("echo a && echo b")
        assert result.exit_code == 0
        assert "a" in result.stdout
        assert "b" in result.stdout
