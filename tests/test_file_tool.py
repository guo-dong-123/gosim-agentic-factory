"""FileTool 单元测试"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.tools.file_tool import FileTool


@pytest.fixture
def workspace():
    """创建临时工作目录"""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def file_tool(workspace):
    return FileTool(workspace)


class TestFileTool:
    def test_write_and_read_file(self, file_tool):
        """测试写入和读取文件"""
        content = "hello world"
        result = file_tool.write_file("test.txt", content)
        assert "已写入" in result

        read_content = file_tool.read_file("test.txt")
        assert read_content == content

    def test_write_nested_file(self, file_tool):
        """测试写入嵌套目录文件"""
        content = "nested"
        file_tool.write_file("a/b/c/test.txt", content)
        assert file_tool.read_file("a/b/c/test.txt") == content

    def test_list_dir(self, file_tool):
        """测试列出目录"""
        file_tool.write_file("file1.txt", "1")
        file_tool.write_file("file2.txt", "2")
        file_tool.create_dir("subdir")

        items = file_tool.list_dir(".")
        names = [item.name for item in items]
        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names

    def test_file_exists(self, file_tool):
        """测试文件存在检查"""
        assert not file_tool.file_exists("nonexistent.txt")
        file_tool.write_file("exists.txt", "test")
        assert file_tool.file_exists("exists.txt")

    def test_delete_file(self, file_tool):
        """测试删除文件"""
        file_tool.write_file("to_delete.txt", "test")
        assert file_tool.file_exists("to_delete.txt")

        result = file_tool.delete_file("to_delete.txt")
        assert "已删除" in result
        assert not file_tool.file_exists("to_delete.txt")

    def test_path_traversal_protection(self, file_tool):
        """测试路径越界保护"""
        with pytest.raises(ValueError):
            file_tool.read_file("../etc/passwd")

    def test_read_nonexistent_file(self, file_tool):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            file_tool.read_file("nonexistent.txt")

    def test_create_dir(self, file_tool):
        """测试创建目录"""
        result = file_tool.create_dir("new/dir")
        assert "已创建目录" in result
        items = file_tool.list_dir("new")
        assert any(item.name == "dir" and item.is_dir for item in items)
