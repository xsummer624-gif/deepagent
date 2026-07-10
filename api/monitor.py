import datetime
import asyncio
import logging
from typing import Any, Dict, List, Optional
from fastapi import WebSocket
from api.context import get_thread_context

logger = logging.getLogger(__name__)

# 尝试导入全局运行时（用于脚本模式下的流式输出）
try:
    import builtins
except ImportError:
    builtins = None


class ToolMonitor:
    """
    工具监控类，用于在工具执行过程中上报进度和状态。
    设计为单例模式，可在任何工具中直接导入使用。
    兼容 FastAPI WebSocket 和 脚本运行时的 stream_writer。

    使用示例:
    from api.monitor import monitor

    def my_tool(arg1):
        monitor.report_start("my_tool", {"arg1": arg1})
        ...
        monitor.report_running("my_tool", "正在处理数据...", progress=0.5)
        ...
        monitor.report_end("my_tool", result)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolMonitor, cls).__new__(cls)
            cls._instance.websocket_manager = None  # 预留给 FastAPI WebSocketManager
        return cls._instance

    def set_websocket_manager(self, manager):
        """设置 FastAPI 的 WebSocket 管理器"""
        self.websocket_manager = manager

    def _emit(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """内部发送方法"""
        payload = {
            "type": "monitor_event",
            "event": event_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.datetime.now().isoformat()
        }

        if self.websocket_manager:
            try:
                thread_id = get_thread_context()
                manager_loop = self.websocket_manager.loop

                if manager_loop and thread_id:
                    coro = self.websocket_manager.send_to_thread(payload, thread_id)
                    try:
                        current_loop = asyncio.get_running_loop()
                    except RuntimeError:
                        # 当前线程没有运行中的事件循环（如子线程）
                        current_loop = None

                    if current_loop is not None and current_loop == manager_loop:
                        # 同一事件循环内，直接调度任务
                        current_loop.create_task(coro)
                    else:
                        # 跨线程：安全地提交到管理器所在的事件循环
                        asyncio.run_coroutine_threadsafe(coro, manager_loop)
            except Exception as e:
                logger.warning(f"[Monitor] WebSocket send failed: {e}")

        if builtins and hasattr(builtins, 'runtime') and hasattr(builtins.runtime, 'stream_writer'):
            try:
                builtins.runtime.stream_writer(payload)
            except Exception as e:
                logger.warning(f"[Monitor] Runtime stream writer failed: {e}")

        logger.info(f"[Monitor:{event_type}] {message}")

    def report_tool(self, tool_name: str, args: Dict[str, Any] = None):
        """报告工具开始执行"""
        self._emit("tool_start", f"开始执行工具: {tool_name}", {"tool_name": tool_name, "args": args})

    def report_assistant(self, assistant_name: str, args: Dict[str, Any] = None):
        """报告正在调用的子智能体进度"""
        self._emit("assistant_call", f"正在调用助手: {assistant_name}",
                   {"assistant_name": assistant_name, "args": args})

    def report_task_result(self, result: str):
        """报告任务最终结果"""
        self._emit("task_result", "任务执行完成", {"result": result})

    def report_session_dir(self, path: str):
        """报告任务工作目录"""
        self._emit("session_created", f"工作目录已创建: {path}", {"path": path})


# 全局单例实例
monitor = ToolMonitor()


class ConnectionManager:
    """
    WebSocket 连接管理器。
    支持同一 thread_id 的多个连接（如多标签页），向该会话所有连接广播消息。
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.loop = None

    def set_loop(self, loop):
        self.loop = loop
        monitor.set_websocket_manager(self)

    async def connect(self, websocket: WebSocket, thread_id: str):
        await websocket.accept()
        self.active_connections.setdefault(thread_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, thread_id: str):
        conns = self.active_connections.get(thread_id)
        if conns:
            try:
                conns.remove(websocket)
            except ValueError:
                pass
            if not conns:
                self.active_connections.pop(thread_id, None)

    async def send_to_thread(self, message: dict, thread_id: str):
        """向同一 thread_id 的所有活跃连接广播消息"""
        conns = self.active_connections.get(thread_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        # 清理已失效的连接
        for ws in dead:
            self.disconnect(ws, thread_id)


manager = ConnectionManager()
