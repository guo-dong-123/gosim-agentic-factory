"""任务队列：管理任务的调度和依赖"""
from typing import List, Optional
from src.harness.context import SharedContext, Task


class TaskQueue:
    """任务队列，支持依赖调度"""

    def __init__(self, context: SharedContext):
        self.context = context

    def add_tasks(self, tasks: List[Task]):
        """批量添加任务"""
        for task in tasks:
            self.context.add_task(task)

    def get_next_task(self) -> Optional[Task]:
        """获取下一个可执行的任务（依赖已完成的 pending 任务）"""
        for task in self.context.tasks:
            if task.status == "pending" and self.context.is_task_ready(task):
                return task
        return None

    def start_task(self, task_id: str) -> Optional[Task]:
        """标记任务开始执行"""
        task = self.context.get_task(task_id)
        if task:
            task.status = "in_progress"
            self.context.current_task_id = task_id
        return task

    def complete_task(self, task_id: str, result: str = ""):
        """标记任务完成"""
        task = self.context.get_task(task_id)
        if task:
            task.status = "done"
            task.result = result
            if self.context.current_task_id == task_id:
                self.context.current_task_id = None

    def block_task(self, task_id: str, reason: str):
        """标记任务阻塞"""
        task = self.context.get_task(task_id)
        if task:
            task.status = "blocked"
            task.result = reason
            if self.context.current_task_id == task_id:
                self.context.current_task_id = None

    def increment_attempt(self, task_id: str) -> int:
        """增加任务尝试次数，返回当前次数"""
        task = self.context.get_task(task_id)
        if task:
            task.attempts += 1
            self.context.total_attempts += 1
            return task.attempts
        return 0

    def get_progress(self) -> dict:
        """获取任务进度"""
        total = len(self.context.tasks)
        done = len([t for t in self.context.tasks if t.status == "done"])
        blocked = len([t for t in self.context.tasks if t.status == "blocked"])
        in_progress = len([t for t in self.context.tasks if t.status == "in_progress"])
        pending = total - done - blocked - in_progress

        return {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "pending": pending,
            "blocked": blocked,
            "progress_percent": round(done / total * 100, 1) if total > 0 else 0,
        }

    def all_done(self) -> bool:
        """是否所有任务都完成（或阻塞）"""
        for task in self.context.tasks:
            if task.status in ("pending", "in_progress", "testing", "review"):
                return False
        return True
