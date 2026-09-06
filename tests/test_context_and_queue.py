"""SharedContext 和 TaskQueue 单元测试"""
import pytest
from src.harness.context import SharedContext, Task
from src.harness.task_queue import TaskQueue


@pytest.fixture
def context():
    return SharedContext(project_root="/tmp/test", requirements="测试需求")


@pytest.fixture
def task_queue(context):
    return TaskQueue(context)


class TestSharedContext:
    def test_add_and_get_task(self, context):
        task = Task(id="t1", title="任务1", description="测试")
        context.add_task(task)
        assert context.get_task("t1") is not None
        assert context.get_task("t1").title == "任务1"

    def test_update_task_status(self, context):
        task = Task(id="t1", title="任务1")
        context.add_task(task)
        context.update_task_status("t1", "done")
        assert context.get_task("t1").status == "done"

    def test_get_pending_tasks(self, context):
        context.add_task(Task(id="t1", title="待办", status="pending"))
        context.add_task(Task(id="t2", title="完成", status="done"))
        pending = context.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].id == "t1"

    def test_is_task_ready(self, context):
        context.add_task(Task(id="t1", title="前置", status="done"))
        context.add_task(Task(id="t2", title="后置", status="pending", dependencies=["t1"]))
        assert context.is_task_ready(context.get_task("t2")) is True

    def test_is_task_not_ready(self, context):
        context.add_task(Task(id="t1", title="前置", status="pending"))
        context.add_task(Task(id="t2", title="后置", status="pending", dependencies=["t1"]))
        assert context.is_task_ready(context.get_task("t2")) is False

    def test_file_cache(self, context):
        context.cache_file("test.py", "print('hello')")
        assert context.get_cached_file("test.py") == "print('hello')"
        assert context.get_cached_file("nonexistent.py") is None

    def test_summary(self, context):
        context.add_task(Task(id="t1", title="完成", status="done"))
        context.add_task(Task(id="t2", title="待办", status="pending"))
        context.total_tokens = 1000
        summary = context.summary()
        assert summary["total_tasks"] == 2
        assert summary["done_tasks"] == 1
        assert summary["total_tokens"] == 1000


class TestTaskQueue:
    def test_get_next_task(self, task_queue, context):
        context.add_task(Task(id="t1", title="任务1", status="pending"))
        context.add_task(Task(id="t2", title="任务2", status="pending"))
        next_task = task_queue.get_next_task()
        assert next_task is not None
        assert next_task.id == "t1"

    def test_get_next_task_with_dependencies(self, task_queue, context):
        context.add_task(Task(id="t1", title="前置", status="pending"))
        context.add_task(Task(id="t2", title="后置", status="pending", dependencies=["t1"]))
        # t2 依赖 t1 未完成，应该返回 t1
        next_task = task_queue.get_next_task()
        assert next_task.id == "t1"

    def test_start_task(self, task_queue, context):
        context.add_task(Task(id="t1", title="任务1", status="pending"))
        task = task_queue.start_task("t1")
        assert task.status == "in_progress"
        assert context.current_task_id == "t1"

    def test_complete_task(self, task_queue, context):
        context.add_task(Task(id="t1", title="任务1", status="in_progress"))
        context.current_task_id = "t1"
        task_queue.complete_task("t1", result="完成了")
        task = context.get_task("t1")
        assert task.status == "done"
        assert task.result == "完成了"
        assert context.current_task_id is None

    def test_block_task(self, task_queue, context):
        context.add_task(Task(id="t1", title="任务1", status="in_progress"))
        context.current_task_id = "t1"
        task_queue.block_task("t1", reason="超过最大尝试次数")
        task = context.get_task("t1")
        assert task.status == "blocked"
        assert task.result == "超过最大尝试次数"

    def test_increment_attempt(self, task_queue, context):
        context.add_task(Task(id="t1", title="任务1", attempts=0))
        count = task_queue.increment_attempt("t1")
        assert count == 1
        assert context.total_attempts == 1

    def test_get_progress(self, task_queue, context):
        context.add_task(Task(id="t1", title="完成", status="done"))
        context.add_task(Task(id="t2", title="进行中", status="in_progress"))
        context.add_task(Task(id="t3", title="待办", status="pending"))
        progress = task_queue.get_progress()
        assert progress["total"] == 3
        assert progress["done"] == 1
        assert progress["in_progress"] == 1
        assert progress["pending"] == 1
        assert progress["progress_percent"] == 33.3

    def test_all_done(self, task_queue, context):
        context.add_task(Task(id="t1", title="完成", status="done"))
        context.add_task(Task(id="t2", title="阻塞", status="blocked"))
        assert task_queue.all_done() is True

    def test_not_all_done(self, task_queue, context):
        context.add_task(Task(id="t1", title="完成", status="done"))
        context.add_task(Task(id="t2", title="待办", status="pending"))
        assert task_queue.all_done() is False
