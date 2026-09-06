"""Coder Agent：程序员，负责编写实现代码"""
from typing import Optional
from src.agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    """程序员 Agent

    职责：
    1. 根据需求和测试用例编写实现代码
    2. 确保代码能通过测试
    3. 代码规范、可维护
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = "Coder"
        self.system_prompt = """你是一个资深 Python 开发工程师，擅长编写高质量、可维护的代码。

你的职责：
1. 根据需求描述和测试用例编写实现代码
2. 确保代码能通过所有测试
3. 代码结构清晰、命名规范、有适当注释
4. 只输出代码，不要多余解释

输出格式：
```python
<实现代码>
```
"""

    def write_code(
        self,
        requirement: str,
        module_name: str,
        test_code: Optional[str] = None,
        interface: Optional[str] = None,
    ) -> str:
        """根据需求和测试用例编写实现代码

        Args:
            requirement: 需求描述
            module_name: 模块名（生成的文件名）
            test_code: 测试用例代码（可选，TDD模式下传入）
            interface: 接口定义（可选）

        Returns:
            实现文件路径
        """
        self.log(f"开始为模块 [{module_name}] 编写实现代码")

        prompt = f"""请根据以下需求编写 Python 实现代码。

需求描述：
{requirement}

模块名：{module_name}（文件名：{module_name}.py）

"""
        if interface:
            prompt += f"""接口定义：
{interface}

"""

        if test_code:
            prompt += f"""测试用例（代码必须能通过这些测试）：
```python
{test_code}
```

"""

        prompt += """要求：
1. 实现所有测试用例覆盖的功能
2. 代码结构清晰、命名规范
3. 只输出代码块"""

        response = self.think(prompt, temperature=0.2)
        code = self.extract_code(response, "python")

        # 写入实现文件
        code_file = f"src/{module_name}.py"
        self.file_tool.write_file(code_file, code)
        self.log(f"实现代码已写入: {code_file} ({len(code)} 字符)")

        # 缓存到上下文
        self.context.cache_file(code_file, code)
        current_task = self.context.get_current_task()
        if current_task:
            if code_file not in current_task.files:
                current_task.files.append(code_file)

        return code_file

    def fix_code(
        self,
        module_name: str,
        error_message: str,
        test_output: str,
        current_code: Optional[str] = None,
    ) -> str:
        """根据错误信息修复代码

        Args:
            module_name: 模块名
            error_message: 错误信息摘要
            test_output: 测试输出详情
            current_code: 当前代码（可选，不传则从文件读取）

        Returns:
            修复后的文件路径
        """
        self.log(f"修复模块 [{module_name}] 的代码")

        # 读取当前代码
        if current_code is None:
            code_file = f"src/{module_name}.py"
            if self.file_tool.file_exists(code_file):
                current_code = self.file_tool.read_file(code_file)
            else:
                current_code = "# 文件不存在"

        prompt = f"""以下 Python 代码运行测试失败，请修复它。

当前代码：
```python
{current_code}
```

错误信息：
{error_message}

测试输出：
{test_output[-3000:]}

要求：
1. 分析失败原因，修复代码
2. 保持代码结构和命名规范
3. 只输出完整的修复后代码块"""

        response = self.think(prompt, temperature=0.3)
        fixed_code = self.extract_code(response, "python")

        # 写入修复后的代码
        code_file = f"src/{module_name}.py"
        self.file_tool.write_file(code_file, fixed_code)
        self.log(f"代码已修复并写入: {code_file}")

        # 缓存到上下文
        self.context.cache_file(code_file, fixed_code)

        # 记录修复历史
        current_task = self.context.get_current_task()
        if current_task:
            self.context.add_fix_record(
                task_id=current_task.id,
                attempt=current_task.attempts,
                error=error_message[:500],
                fix=f"修复 {module_name}.py",
            )

        return code_file
