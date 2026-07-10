import logging
from pathlib import Path

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated
from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path

logger = logging.getLogger(__name__)


# Markdown生成工具
@tool
def generate_markdown(
        content: Annotated[str, "要写入Markdown文档的文本内容"],
        filename: Annotated[str, "Markdown文档的文件名（不包含扩展名或包含.md）"],
        path: Annotated[str, "文件保存的绝对路径"] = ""
):
    """根据提供的文本内容，生成对应的Markdown(.md)文件"""
    monitor.report_tool("Markdown文档生成工具", {"写入的文本内容": content})
    if not filename.endswith('.md'):
        filename += '.md'

    session_dir = get_session_context()

    # --- 路径清洗与重定向逻辑 ---
    if path and path != ".":
        full_input_path = str(Path(path) / filename)
    else:
        full_input_path = filename
    full_path_str = resolve_path(full_input_path, session_dir)
    file_path = Path(full_path_str)

    parent_dir = file_path.parent

    try:
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {parent_dir}")

        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Successfully wrote to: {file_path}")
        return f"Markdown文件 '{file_path}' 已成功生成并保存。"
    except Exception as e:
        logger.exception(f"Error writing file: {e}")
        return f"生成Markdown文件失败: {str(e)}"


if __name__ == "__main__":
    from unittest.mock import patch
    import tools.markdown_tools as md_tools

    test_content = "# 测试文档\n这是给session_dir配置固定值后的测试内容"
    test_filename = "测试文件"
    test_path = "sub_dir"

    with patch.object(md_tools, 'get_session_context', return_value="./test_session_123"):
        print("===== 开始测试（session_dir已配置为：./test_session_123） =====")
        result = generate_markdown.invoke({
            "content": test_content,
            "filename": test_filename,
            "path": test_path
        })
        print(f"\n调用结果：{result}")