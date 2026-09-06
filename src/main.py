"""简单 TDD 工作流：Tester 写测试 → Coder 写代码 → 跑测试 → 失败则修复循环

Phase 2 验证脚本：给定一个简单需求，自主完成开发并通过测试。
"""
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import WORKSPACE_DIR, MAX_FIX_ATTEMPTS
from src.models.llm_client import LLMClient
from src.harness.context import SharedContext, Task
from src.harness.task_queue import TaskQueue
from src.tools.file_tool import FileTool
from src.tools.command_tool import CommandTool
from src.tools.test_tool import TestTool
from src.tools.git_tool import GitTool
from src.agents.tester_agent import TesterAgent
from src.agents.coder_agent import CoderAgent


def run_tdd_flow(requirement: str, module_name: str, max_attempts: int = MAX_FIX_ATTEMPTS):
    """运行 TDD 主流程

    Args:
        requirement: 需求描述
        module_name: 模块名
        max_attempts: 最大修复轮次
    """
    print("=" * 60)
    print("🚀 TDD 工作流启动")
    print(f"📋 需求: {requirement}")
    print(f"📦 模块: {module_name}")
    print("=" * 60)

    # 1. 初始化工具
    file_tool = FileTool(str(WORKSPACE_DIR))
    command_tool = CommandTool(str(WORKSPACE_DIR))
    test_tool = TestTool(command_tool)
    git_tool = GitTool(command_tool)

    # 2. 初始化上下文
    context = SharedContext(
        project_root=str(WORKSPACE_DIR),
        requirements=requirement,
    )
    task = Task(
        id="task_001",
        title=f"实现 {module_name}",
        description=requirement,
        status="in_progress",
    )
    context.add_task(task)
    context.current_task_id = task.id
    task_queue = TaskQueue(context)

    # 3. 初始化 LLM 和 Agents
    llm = LLMClient()
    tester = TesterAgent(llm, context, file_tool, command_tool, test_tool, git_tool)
    coder = CoderAgent(llm, context, file_tool, command_tool, test_tool, git_tool)

    # 4. TDD 流程
    print("\n🔴 Step 1: Tester 编写测试用例（预期全红）")
    test_file = tester.write_tests(requirement, module_name)

    # 先跑一次测试，确认测试是有效的（应该全失败，因为还没实现）
    print("\n🔴 运行测试（预期失败，验证测试有效性）...")
    initial_report = tester.run_tests(test_file)
    print(f"   初始测试: {initial_report['failed']} 失败（符合预期）")

    print("\n🟢 Step 2: Coder 编写实现代码")
    test_code = file_tool.read_file(test_file)
    code_file = coder.write_code(requirement, module_name, test_code=test_code)

    # 5. 测试-修复循环
    print("\n🔄 Step 3: 测试-修复循环")
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- 第 {attempt}/{max_attempts} 轮测试 ---")

        report = tester.run_tests(test_file)

        if report["success"]:
            print(f"\n✅ 所有测试通过！共 {report['passed']} 个测试")
            task_queue.complete_task(task.id, result=f"{report['passed']} 个测试全部通过")
            break

        # 测试失败，分析并修复
        print(f"❌ 测试失败: {report['failed']} 失败, {report['errors']} 错误")

        if attempt >= max_attempts:
            print(f"\n⚠️ 达到最大修复轮次 ({max_attempts})，任务阻塞")
            task_queue.block_task(task.id, reason=f"超过最大修复轮次，仍有 {report['failed']} 个测试失败")
            break

        # 分析失败原因
        print("🔍 分析失败原因...")
        analysis = tester.analyze_failure(report)
        print(f"   分析: {analysis[:200]}...")

        # 修复代码
        print("🛠️ 修复代码...")
        task_queue.increment_attempt(task.id)
        coder.fix_code(
            module_name=module_name,
            error_message=analysis,
            test_output=report["raw_output"],
        )

    # 6. 输出总结
    print("\n" + "=" * 60)
    print("📊 工作流总结")
    print("=" * 60)
    progress = task_queue.get_progress()
    summary = context.summary()
    print(f"任务状态: {task.status}")
    print(f"尝试次数: {task.attempts}")
    print(f"Token 消耗: {summary['total_tokens']}")
    print(f"生成文件: {task.files + task.test_files}")
    print("=" * 60)

    return task.status == "done"


if __name__ == "__main__":
    # 默认测试需求：实现一个计算器类
    default_req = "实现一个 Calculator 类，支持加法(add)、减法(subtract)、乘法(multiply)、除法(divide)。除法在除数为0时抛出 ValueError。"
    default_module = "calculator"

    requirement = sys.argv[1] if len(sys.argv) > 1 else default_req
    module_name = sys.argv[2] if len(sys.argv) > 2 else default_module

    success = run_tdd_flow(requirement, module_name)
    sys.exit(0 if success else 1)
