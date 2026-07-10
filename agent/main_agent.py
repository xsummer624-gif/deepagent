import logging
from langgraph.checkpoint.memory import InMemorySaver

from agent.subagents.knowledge_base_agent import knowledge_base_agent
from agent.subagents.database_query_agent import database_query_agent
from agent.subagents.network_search_agent import network_search_agent

from tools.markdown_tools import generate_markdown
from tools.upload_file_read_tool import read_file_content

from deepagents import create_deep_agent
from agent.llm import model
from agent.prompts import main_agent_content

from api.monitor import monitor
import asyncio
import uuid
import shutil
from pathlib import Path

from api.context import set_session_context, reset_session_context, set_thread_context, reset_thread_context
from api.logger import AgentLogger, AgentLogCallbackHandler

from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

subagents_list = [
    knowledge_base_agent,
    database_query_agent,
    network_search_agent
]

# 延迟初始化：避免模块导入时即创建 Agent（含 LLM 连接），提升启动速度与可测试性
_main_agent = None


def get_main_agent():
    """惰性创建并缓存主智能体实例。"""
    global _main_agent
    if _main_agent is None:
        _main_agent = create_deep_agent(
            model=model,
            subagents=subagents_list,
            system_prompt=main_agent_content['system_prompt'],
            tools=[generate_markdown, read_file_content],
            checkpointer=InMemorySaver()
        )
    return _main_agent


# 获取绝对地址 解析路径标识以及软连接
project_root = Path(__file__).parents[1].resolve()


def _prepare_session_environment(thread_id: str):
    """
    初始化会话运行环境（会话文件夹,以及相对路径，上传文件的信息！）。

    Returns:
        tuple: (
            session_dir_str (str): 物理工作目录的绝对路径 (当前会话对应文件存储位置)。
            relative_session_dir (str): 相对于项目根目录的路径 (用于提示词)。
            uploaded_info (str): 注入到 Prompt 中的文件列表描述。
        )
    """
    # 1. [创建] 定义并创建会话的绝对输出路径
    session_dir = project_root / "output" / f"session_{thread_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # 2. [标准化] 路径转为 POSIX 风格 (防止大模型因反斜杠产生幻觉)
    session_dir_str = str(session_dir).replace("\\", "/")

    # 3. [相对化] 获取相对路径 (用于提示词展示，如 "output/session_123")
    relative_session_dir = str(session_dir.relative_to(project_root)).replace("\\", "/")

    # 4. [迁移] 检查并处理上传文件
    upload_dir = project_root / "updated" / f"session_{thread_id}"
    uploaded_info = ""

    if upload_dir.exists():
        files = [f.name for f in upload_dir.iterdir() if f.is_file()]

        if files:
            for f in files:
                shutil.copy2(upload_dir / f, session_dir / f)

            uploaded_info = (f"\n    [已上传文件] 已加载到工作目录:\n" +
                             "\n".join([f"    - {f}" for f in files]) +
                             "\n    请优先使用工具读取并参考这些文件。")

    return session_dir_str, relative_session_dir, uploaded_info


def _process_stream_chunk(chunk):
    """
    处理 LangGraph 流式输出的增量状态。
    - 监听 tool_calls -> 若是 'task' 则上报子 Agent 状态。
    - 监听 content -> 若无工具调用，则视为 Agent 的最终回复。
    """
    for node_name, state in chunk.items():
        if not state or "messages" not in state:
            continue
        messages = state["messages"]
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if isinstance(last_msg, AIMessage):
                if last_msg.tool_calls:
                    for tool in last_msg.tool_calls:
                        if tool['name'] == 'task':
                            monitor.report_assistant(
                                tool['args'].get('subagent_type', 'Agent'),
                                {"desc": tool['args'].get('description')}
                            )
                elif last_msg.content:
                    monitor.report_task_result(last_msg.content)


# ====================== 核心执行逻辑 ======================
async def run_deep_agent(task_query: str, thread_id: str = None):
    """
    DeepAgents 核心执行入口。

    执行步骤：
    1. ID 初始化：确保每个任务有唯一的 thread_id。
    2. 环境准备：创建目录、迁移文件、生成路径信息。
    3. 上下文绑定：将 thread_id 和 session_dir 绑定到当前协程 (ContextVar)。
    4. 提示词构建：将环境信息注入到 Prompt。
    5. 流式执行：驱动 LangGraph 运行，并实时解析/上报每一个 Chunk。
    6. 资源清理：任务结束后（无论成功失败）重置上下文。
    """
    if not thread_id:
        thread_id = str(uuid.uuid4())
    logger.info(f"--- Start Task: {task_query} (Thread: {thread_id}) ---")

    session_dir_str, relative_session_dir, uploaded_info = _prepare_session_environment(thread_id)

    thread_token = set_thread_context(thread_id)
    session_token = set_session_context(session_dir_str)
    # 推送相对 output 目录的路径，供前端拼接静态文件 URL
    monitor.report_session_dir(relative_session_dir)

    agent_logger = AgentLogger(thread_id, str(project_root))
    log_callback = AgentLogCallbackHandler(agent_logger)

    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [log_callback],
    }

    path_instruction = f"""
    【工作环境指令】
    工作目录: {relative_session_dir}
    {uploaded_info}

    规则：
    1. 新生成文件必须保存到工作目录：'{relative_session_dir}/filename'
    2. 使用相对路径，禁止使用绝对路径
    3. 若存在上传文件，请先分析内容
    """

    try:
        agent = get_main_agent()
        async for chunk in agent.astream(
                {"messages": [{"role": "user", "content": task_query + path_instruction}]},
                config=config
        ):
            _process_stream_chunk(chunk)
        return "Done"
    except Exception as e:
        logger.exception(f"Execution failed: {e}")
        monitor._emit("error", f"Execution failed: {e}")
        return f"Error: {e}"
    finally:
        reset_session_context(session_token)
        reset_thread_context(thread_token)
