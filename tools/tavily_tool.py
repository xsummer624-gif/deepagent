from typing import Literal
from langchain_core.tools import tool
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from api.monitor import monitor

load_dotenv()

# 延迟创建：避免模块导入时即初始化客户端（Key 缺失时报错时机后移到首次调用）
_tavily_client: TavilyClient | None = None


def _get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY 未配置，请在 .env 中设置")
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


@tool
def internet_search(
        query: str,
        topic: Literal["news", "finance", "general"] = "general",
        max_results: int = 5,
        include_raw_content: bool = False
):
    """
    根据用户问题，进行网络信息收集。
    注意：主要搜集网络公开信息，如果指定查询数据库或者rag不要使用此工具
    :param query: 用户的查询信息
    :param topic: 查询类型
    :param max_results: 返回的最大条数
    :param include_raw_content: 是否返回原内容 False 精简 True 详细
    :return:
    """
    monitor.report_tool(tool_name="网络搜索工具", args={"query": query, "topic": topic,
                               "max_results": max_results, "include_raw_content": include_raw_content})

    client = _get_tavily_client()
    return client.search(query=query, topic=topic,
                         max_results=max_results, include_raw_content=include_raw_content)
