from contextvars import ContextVar
from typing import Optional

# 存储当前会话对应的文件夹
_session_dir_ctx: ContextVar[Optional[str]] = ContextVar("session_dir", default=None)

# 存储当前会话对应的websocket
_thread_id_ctx: ContextVar[Optional[str]] = ContextVar("thread_id", default=None)


def set_session_context(path: str):
    """
    设置当前请求链路的会话目录。
    通常在 Agent 开始执行任务前调用。

    Returns:
        Token: 返回一个 Token 对象，后续可用它来恢复(reset)变量状态。
    """
    return _session_dir_ctx.set(path)


def get_session_context() -> Optional[str]:
    """
    获取当前请求链路的会话目录。
    可以在任何深层调用的工具函数中直接使用，无需层层传递参数。
    """
    return _session_dir_ctx.get()


def set_thread_context(thread_id: str):
    """
    设置当前请求链路的 Thread ID。
    """
    return _thread_id_ctx.set(thread_id)


def get_thread_context() -> Optional[str]:
    """
    获取当前请求链路的 Thread ID。
    """
    return _thread_id_ctx.get()


def reset_session_context(session_token):
    """清理会话目录上下文"""
    _session_dir_ctx.reset(session_token)


def reset_thread_context(thread_token):
    """清理线程 ID 上下文"""
    _thread_id_ctx.reset(thread_token)