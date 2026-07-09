from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path


@tool
def read_file_content(
        filename: Annotated[str, "要读取的文件名或路径（支持 .md, .txt）"],
        instruction: Annotated[str, "对提取内容的具体指令"] = "提取全部内容"
) -> str:
    """读取指定文件的内容。支持 Markdown(.md) 和纯文本(.txt)。"""
    monitor.report_tool("文件内容读取工具", {"filename": filename, "instruction": instruction})

    session_dir = get_session_context()
    file_path = Path(resolve_path(filename, session_dir))

    if not file_path.exists():
        return f"错误：文件 '{filename}' 不存在 (解析路径: {file_path})。"

    ext = file_path.suffix.lower()
    if ext in ['.md', '.txt']:
        return file_path.read_text(encoding='utf-8')

    return f"错误：不支持的文件格式 '{ext}'，仅支持 .md 和 .txt。"


if __name__ == '__main__':
    from unittest.mock import patch
    import tools.upload_file_read_tool as uf_t

    with patch.object(uf_t, 'get_session_context', return_value="./test_session_123"):
        result = read_file_content.invoke({"filename": "sub_dir/测试文件.md"})
        print(result)
