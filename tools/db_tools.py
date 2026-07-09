import os
import re
from dotenv import load_dotenv
from api.monitor import monitor
from mysql.connector import connect, Error
from typing import Annotated, List
from langchain_core.tools import tool

load_dotenv()


def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "autocommit": True,
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL")
    }
    config = {k: v for k, v in config.items() if v is not None}

    required_keys = ["user", "password", "database"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ValueError(f"缺失数据库核心配置：{', '.join(missing_keys)}")

    return config


def _execute_query(sql: str, description: str = "") -> str:
    """执行SQL查询并以CSV格式返回结果"""
    config = get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                desc = cursor.description
                if not desc:
                    return f"查询没有结果，sql为: {sql}" if description else f"{description}"
                columns = [col[0] for col in desc]
                rows = cursor.fetchall()
                results = [",".join(map(str, row)) for row in rows]
                return f"{','.join(columns)}\n{'\n'.join(results)}"
    except Error as e:
        return f"查询出现异常: {str(e)}"


@tool
def list_sql_tables() -> str:
    """
    列出配置的 MySQL 数据库中所有可用的表。
    返回值：
        str: 成功时返回 "可用数据表：表1, 表2, ..."；
              配置缺失时返回错误提示；
              执行异常时返回具体错误信息。
    """
    monitor.report_tool(tool_name="数据库表获取工具", args={})
    result = _execute_query("show tables")
    if "查询出现异常" in result or "查询没有结果" in result:
        return result
    # 解析CSV格式的返回，提取表名
    lines = result.strip().split("\n")
    if len(lines) < 2:
        return "没有可用的表"
    table_names = [line.strip() for line in lines[1:] if line.strip()]
    return f"可用的表有: {', '.join(table_names)}" if table_names else "没有可用的表"


def _validate_table_name(table_name: str) -> bool:
    """验证表名是否合法（仅允许字母、数字、下划线）"""
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))


@tool
def get_table_data(table_name: str) -> str:
    """
    查询指定表名的数据。调用前必须先调用 list_sql_tables 完成表名校验。
    返回 CSV 格式数据（含列头），至多 100 条。
    """
    monitor.report_tool(tool_name="数据库表数据查询工具: get_table_data", args={"table_name": table_name})

    if not _validate_table_name(table_name):
        return f"错误：非法的表名 '{table_name}'"

    result = _execute_query(f"select * from {table_name} limit 100")
    if "查询出现异常" in result:
        return result
    lines = result.strip().split("\n")
    if len(lines) < 2:
        return f"数据表: {table_name} 为空没有数据!"
    return result


@tool
def execute_sql_query(query: str) -> str:
    """
    执行自定义查询语句。仅允许 SELECT 查询。
    执行前需通过 list_sql_tables 明确表名，通过 get_table_data 明确表结构和数据格式。
    返回 CSV 格式数据，至多 100 条。
    """
    monitor.report_tool(tool_name="数据库表数据查询工具: execute_sql_query", args={"query": query})

    stripped = query.strip().upper()
    if not stripped.startswith("SELECT"):
        return f"错误：仅允许 SELECT 查询，当前语句以 '{stripped.split()[0] if stripped else ''}' 开头"

    if "INTO OUTFILE" in stripped or "INTO DUMPFILE" in stripped:
        return "错误：禁止使用文件写入操作"

    result = _execute_query(query)
    if "查询出现异常" in result:
        return result
    lines = result.strip().split("\n")
    if len(lines) < 2:
        return f"执行自定义查询SQL语句查询没有结果，sql为: {query}"
    return result

