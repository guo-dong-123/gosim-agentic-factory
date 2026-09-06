"""文件操作工具"""
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """文件信息"""
    name: str
    path: str
    is_dir: bool
    size: int = 0


class FileTool:
    """文件读写工具，所有操作限制在工作目录内"""

    def __init__(self, workspace_dir: str):
        self.workspace = Path(workspace_dir).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        """解析相对路径，确保不越出工作目录"""
        target = (self.workspace / relative_path).resolve()
        if not str(target).startswith(str(self.workspace)):
            raise ValueError(f"路径越界: {relative_path}")
        return target

    def read_file(self, relative_path: str) -> str:
        """读取文件内容"""
        path = self._resolve(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        if not path.is_file():
            raise ValueError(f"不是文件: {relative_path}")
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> str:
        """写入文件，自动创建父目录"""
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"已写入: {relative_path} ({len(content)} 字符)"

    def list_dir(self, relative_path: str = ".") -> List[FileInfo]:
        """列出目录内容"""
        path = self._resolve(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {relative_path}")
        if not path.is_dir():
            raise ValueError(f"不是目录: {relative_path}")

        result = []
        for item in sorted(path.iterdir()):
            result.append(FileInfo(
                name=item.name,
                path=str(item.relative_to(self.workspace)),
                is_dir=item.is_dir(),
                size=item.stat().st_size if item.is_file() else 0,
            ))
        return result

    def create_dir(self, relative_path: str) -> str:
        """创建目录"""
        path = self._resolve(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return f"已创建目录: {relative_path}"

    def file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        path = self._resolve(relative_path)
        return path.exists() and path.is_file()

    def delete_file(self, relative_path: str) -> str:
        """删除文件"""
        path = self._resolve(relative_path)
        if path.exists() and path.is_file():
            path.unlink()
            return f"已删除: {relative_path}"
        return f"文件不存在: {relative_path}"
