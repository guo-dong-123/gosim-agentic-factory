"""共享上下文：所有 Agent 共享的全局状态"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    """任务数据结构"""
    id: str
    title: str
    description: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending / in_progress / testing / review / done / blocked
    files: List[str] = Field(default_factory=list)
    test_files: List[str] = Field(default_factory=list)
    attempts: int = 0
    architecture: str = ""
    result: str = ""


class ArchitectureDecision(BaseModel):
    """架构决策记录"""
    task_id: str
    decision: str
    interfaces: Dict[str, str] = Field(default_factory=dict)
    data_models: Dict[str, str] = Field(default_factory=dict)


class SharedContext(BaseModel):
    """全局共享上下文，所有 Agent 通过它交换信息"""

    # 项目基本信息
    project_root: str = ""
    requirements: str = ""

    # 任务管理
    tasks: List[Task] = Field(default_factory=list)
    current_task_id: Optional[str] = None

    # 架构决策
    architecture_decisions: List[ArchitectureDecision] = Field(default_factory=list)

    # 文件内容缓存（避免重复读文件）
    file_cache: Dict[str, str] = Field(default_factory=dict)

    # 历史记录
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    fix_history: List[Dict[str, Any]] = Field(default_factory=list)

    # 统计
    total_tokens: int = 0
    total_attempts: int = 0

    def get_task(self, task_id: str) -> Optional[Task]:
        """根据 ID 获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_current_task(self) -> Optional[Task]:
        """获取当前任务"""
        if self.current_task_id:
            return self.get_task(self.current_task_id)
        return None

    def update_task_status(self, task_id: str, status: str):
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.status = status

    def add_task(self, task: Task):
        """添加任务"""
        self.tasks.append(task)

    def get_pending_tasks(self) -> List[Task]:
        """获取所有待处理任务"""
        return [t for t in self.tasks if t.status == "pending"]

    def get_blocked_tasks(self) -> List[Task]:
        """获取所有阻塞任务"""
        return [t for t in self.tasks if t.status == "blocked"]

    def is_task_ready(self, task: Task) -> bool:
        """检查任务依赖是否都已完成"""
        for dep_id in task.dependencies:
            dep = self.get_task(dep_id)
            if not dep or dep.status != "done":
                return False
        return True

    def cache_file(self, path: str, content: str):
        """缓存文件内容"""
        self.file_cache[path] = content

    def get_cached_file(self, path: str) -> Optional[str]:
        """获取缓存的文件内容"""
        return self.file_cache.get(path)

    def add_test_result(self, task_id: str, passed: int, failed: int, total: int):
        """记录测试结果"""
        self.test_results.append({
            "task_id": task_id,
            "passed": passed,
            "failed": failed,
            "total": total,
        })

    def add_fix_record(self, task_id: str, attempt: int, error: str, fix: str):
        """记录修复历史"""
        self.fix_history.append({
            "task_id": task_id,
            "attempt": attempt,
            "error": error,
            "fix": fix,
        })

    def summary(self) -> Dict[str, Any]:
        """生成上下文摘要（用于 prompt 注入，避免上下文过大）"""
        done = len([t for t in self.tasks if t.status == "done"])
        blocked = len([t for t in self.tasks if t.status == "blocked"])
        return {
            "total_tasks": len(self.tasks),
            "done_tasks": done,
            "blocked_tasks": blocked,
            "pending_tasks": len(self.tasks) - done - blocked,
            "total_tokens": self.total_tokens,
            "total_attempts": self.total_attempts,
        }
