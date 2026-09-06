"""全局配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# Agent 工作目录（生成的代码放这里）
WORKSPACE_DIR = PROJECT_ROOT / "workspace"

# 轨迹记录目录
TRACES_DIR = PROJECT_ROOT / "traces"

# 模型配置
MODEL_CONFIG = {
    # 比赛官方模型（通过网关调用）
    "kimi": {
        "model": "kimi-k2",
        "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
        "api_key": os.getenv("KIMI_API_KEY", ""),
    },
    "glm": {
        "model": "glm-4-plus",
        "base_url": os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "api_key": os.getenv("GLM_API_KEY", ""),
    },
    "minimax": {
        "model": "MiniMax-M2",
        "base_url": os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"),
        "api_key": os.getenv("MINIMAX_API_KEY", ""),
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    },
}

# 默认模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek")

# 命令执行超时（秒）
COMMAND_TIMEOUT = 60

# 单个 Task 最大修复轮次
MAX_FIX_ATTEMPTS = 5
