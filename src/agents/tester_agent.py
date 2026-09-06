"""Tester Agent：测试工程师，负责编写测试用例"""
from typing import Optional
from src.agents.base_agent import BaseAgent


class TesterAgent(BaseAgent):
    """测试工程师 Agent

    职责：
    1. 根据需求和接口定义编写 pytest 测试用例
    2. 运行测试，返回测试报告
    3. 分析测试失败原因
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = "Tester"
        self.system_prompt = """你是一个资深测试工程师，擅长编写高质量的 pytest 测试用例。

你的职责：
1. 根据需求描述编写完整的 pytest 测试用例
2. 覆盖正常情况、边界情况、异常情况
3. 测试用例必须可直接运行，使用 pytest 格式
4. 测试文件命名：test_<模块名>.py
5. 只输出代码，不要多余解释

输出格式：
```python
<测试代码>
```
"""

    def write_tests(
        self,
        requirement: str,
        module_name: str,
        interface: Optional[str] = None,
    ) -> str:
        """根据需求编写测试用例，写入测试文件

        Args:
            requirement: 需求描述
            module_name: 模块名（用于生成测试文件名和import）
            interface: 接口定义（可选，有则更精准）

        Returns:
            测试文件路径
        """
        self.log(f"开始为模块 [{module_name}] 编写测试用例")

        prompt = f"""请根据以下需求编写 pytest 测试用例。

需求描述：
{requirement}

"""
        if interface:
            prompt += f"""接口定义：
{interface}

"""

        prompt += f"""要求：
1. 测试文件 import 的模块名是：{module_name}
2. 覆盖正常、边界、异常情况
3. 使用 pytest 标准格式
4. 只输出代码块"""

        response = self.think(prompt, temperature=0.2)
        test_code = self.extract_code(response, "python")

        # 写入测试文件
        test_file = f"tests/test_{module_name}.py"
        self.file_tool.write_file(test_file, test_code)
        self.log(f"测试用例已写入: {test_file} ({len(test_code)} 字符)")

        # 缓存到上下文
        self.context.cache_file(test_file, test_code)
        current_task = self.context.get_current_task()
        if current_task:
            if test_file not in current_task.test_files:
                current_task.test_files.append(test_file)

        return test_file

    def run_tests(self, test_file: Optional[str] = None) -> dict:
        """运行测试，返回测试报告

        Args:
            test_file: 指定测试文件，默认运行所有测试

        Returns:
            测试报告字典
        """
        self.log(f"运行测试: {test_file or '全部测试'}")

        target = test_file or "tests/"
        report = self.test_tool.run_tests(target)

        self.log(f"测试结果: {report.passed} 通过, {report.failed} 失败, {report.errors} 错误")

        # 记录到上下文
        current_task = self.context.get_current_task()
        if current_task:
            self.context.add_test_result(
                task_id=current_task.id,
                passed=report.passed,
                failed=report.failed,
                total=report.total,
            )

        return {
            "success": report.success,
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "errors": report.errors,
            "failed_tests": [tc.name for tc in report.test_cases if tc.status in ("failed", "error")],
            "raw_output": report.raw_output[-2000:] if len(report.raw_output) > 2000 else report.raw_output,
        }

    def analyze_failure(self, test_report: dict) -> str:
        """分析测试失败原因，给出修复建议

        Args:
            test_report: 测试报告字典

        Returns:
            失败分析和修复建议
        """
        if test_report["success"]:
            return "所有测试通过，无需修复。"

        self.log("分析测试失败原因...")

        prompt = f"""以下是 pytest 测试运行的输出，请分析失败原因并给出修复建议。

失败的测试：
{test_report['failed_tests']}

测试输出：
{test_report['raw_output']}

请分析：
1. 每个失败的根本原因是什么
2. 应该如何修复
3. 只输出分析和建议，不要输出代码"""

        analysis = self.think(prompt, temperature=0.3)
        self.log(f"失败分析完成")
        return analysis
