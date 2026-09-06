"""测试运行工具"""
import re
from typing import List, Optional
from pydantic import BaseModel
from src.tools.command_tool import CommandTool, CommandResult


class TestCaseResult(BaseModel):
    """单个测试用例结果"""
    name: str
    status: str  # passed / failed / error
    duration: str = ""
    message: str = ""


class TestReport(BaseModel):
    """测试报告"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    success: bool = False
    raw_output: str = ""
    test_cases: List[TestCaseResult] = []


class TestTool:
    """测试运行工具，支持 pytest"""

    def __init__(self, command_tool: CommandTool):
        self.cmd = command_tool

    def run_tests(
        self,
        test_path: str = ".",
        extra_args: str = "",
    ) -> TestReport:
        """运行 pytest 测试

        Args:
            test_path: 测试文件或目录路径
            extra_args: 额外的 pytest 参数
        """
        command = f"python -m pytest {test_path} -v --tb=short {extra_args}".strip()
        result = self.cmd.run(command)

        return self._parse_pytest_output(result)

    def _parse_pytest_output(self, result: CommandResult) -> TestReport:
        """解析 pytest 输出"""
        output = result.stdout + result.stderr
        report = TestReport(raw_output=output)

        # 解析测试用例结果（pytest -v 格式）
        # 例: tests/test_example.py::test_add PASSED
        case_pattern = re.compile(
            r'^(.+?::.+?)\s+(PASSED|FAILED|ERROR|SKIPPED)',
            re.MULTILINE,
        )
        for match in case_pattern.finditer(output):
            name = match.group(1).strip()
            status = match.group(2).lower()
            if status == "skipped":
                continue
            report.test_cases.append(TestCaseResult(
                name=name,
                status=status if status != "error" else "error",
            ))

        # 解析汇总行
        # 例: 5 passed, 2 failed in 0.5s
        summary_pattern = re.compile(
            r'(\d+)\s+passed',
        )
        passed_match = summary_pattern.search(output)
        if passed_match:
            report.passed = int(passed_match.group(1))

        failed_match = re.search(r'(\d+)\s+failed', output)
        if failed_match:
            report.failed = int(failed_match.group(1))

        error_match = re.search(r'(\d+)\s+error', output)
        if error_match:
            report.errors = int(error_match.group(1))

        report.total = report.passed + report.failed + report.errors
        report.success = (result.exit_code == 0) and (report.failed == 0) and (report.errors == 0)

        return report

    def get_failed_tests(self, report: TestReport) -> List[TestCaseResult]:
        """获取失败的测试用例"""
        return [tc for tc in report.test_cases if tc.status in ("failed", "error")]
