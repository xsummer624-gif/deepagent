import os
import datetime
import json
import logging as std_logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

_logger = std_logging.getLogger(__name__)


class AgentLogger:
    """
    Agent 日志记录核心类 (基于标准 logging 模块封装)。

    设计目的：
    1. **解耦**：将日志写入逻辑与 Agent 的业务逻辑分离。
    2. **多层级记录**：
       - 高层级：记录主智能体的状态流转。
       - 低层级：通过 Callback 机制捕获子智能体的细节。
    3. **会话隔离**：基于 thread_id 生成独立日志文件。
    4. **标准库支持**：使用 logging 模块实现线程安全的文件写入和格式化。
    """
    def __init__(self, thread_id: str, project_root: str):
        self.thread_id = thread_id
        self.log_dir = os.path.join(project_root, "log")
        self.log_file = os.path.join(self.log_dir, f"agent_trace_{thread_id}.log")

        self._ensure_log_dir()

        self.logger = self._setup_logger()

        self._write_log("SYSTEM", f"Logger initialized for thread: {thread_id}")

    def _ensure_log_dir(self):
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
        except Exception as e:
            _logger.warning(f"Failed to create log directory: {e}")

    def _setup_logger(self) -> logging.Logger:
        logger_name = f"agent_trace_{self.thread_id}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            try:
                file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
                file_handler.setLevel(logging.INFO)

                formatter = logging.Formatter(
                    fmt='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)

                logger.addHandler(file_handler)
            except Exception as e:
                _logger.warning(f"Error setting up logger: {e}")

        return logger

    def _write_log(self, category: str, content: str):
        formatted_message = f"[{category}]\n{content}\n{'-'*40}"
        self.logger.info(formatted_message)

    def log_main_chunk(self, chunk: Any):
        self._write_log("MAIN_AGENT_STATE_UPDATE", str(chunk))

    def log_tool_call(self, tool_name: str, args: Dict[str, Any]):
        try:
            args_str = json.dumps(args, ensure_ascii=False, indent=2)
        except Exception:
            args_str = str(args)

        content = f"Tool Name: {tool_name}\nArguments:\n{args_str}"
        self._write_log("TOOL_CALL_DETAILS", content)


class AgentLogCallbackHandler(BaseCallbackHandler):
    """LangChain 回调处理器，捕获子智能体的思考过程"""

    def __init__(self, logger: AgentLogger):
        self.logger = logger

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Optional[Any]:
        tags = kwargs.get("tags", [])
        prompt_preview = prompts[0][:1000] + "..." if prompts else "No prompts"
        self.logger._write_log("LLM_START", f"Tags: {tags}\nPrompts Preview:\n{prompt_preview}")
        return None

    def on_llm_new_token(self, token: str, **kwargs: Any) -> Optional[Any]:
        if token:
            self.logger._write_log("LLM_TOKEN_CHUNK", token)
        return None

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Optional[Any]:
        generations = response.generations
        for gen_list in generations:
            for gen in gen_list:
                self.logger._write_log("LLM_OUTPUT", gen.text)
        return None

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Optional[Any]:
        name = serialized.get("name", "unknown")
        self.logger._write_log("TOOL_START", f"Tool: {name}\nInput: {input_str}")
        return None

    def on_tool_end(self, output: str, **kwargs: Any) -> Optional[Any]:
        preview = output[:2000] + "..." if len(str(output)) > 2000 else output
        self.logger._write_log("TOOL_END", f"Output: {preview}")
        return None

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Optional[Any]:
        name = serialized.get("name", "unknown") if serialized else "unknown"
        tags = kwargs.get("tags", [])
        if tags and "seq:step" not in tags:
            self.logger._write_log("CHAIN_START", f"Chain: {name}\nTags: {tags}\nInputs: {str(inputs)[:500]}...")
        return None
