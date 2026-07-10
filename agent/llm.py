from dotenv import load_dotenv, find_dotenv
import os
from langchain.chat_models import init_chat_model

# find_dotenv()确保找到.env 递归查询当前项目文件
load_dotenv(find_dotenv())


def _resolve_env(primary: str, fallback: str) -> str | None:
    """优先读取 primary 环境变量，缺失时回退到 fallback。"""
    return os.getenv(primary) or os.getenv(fallback)


# 兼容 DEEPSEEK_* / OPENAI_* 两套环境变量命名
model = init_chat_model(
    model=_resolve_env("DEEPSEEK_MODEL_R", "LLM_QWEN_MAX") or os.getenv("OPENAI_MODEL"),
    base_url=_resolve_env("DEEPSEEK_BASE_URL", "OPENAI_BASE_URL"),
    api_key=_resolve_env("DEEPSEEK_API_KEY", "OPENAI_API_KEY"),
)
