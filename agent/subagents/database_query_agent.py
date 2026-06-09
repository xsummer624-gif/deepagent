from agent.prompts import sub_agents_content
from tools.db_tools import list_sql_tables,get_table_data,execute_sql_query

database_query_agent = {
    "name":sub_agents_content["db"].get("name",""),
    "description":sub_agents_content["db"].get("description",""),
    "system_prompt":sub_agents_content["db"].get("system_prompt",""),
    "tools": [list_sql_tables,get_table_data,execute_sql_query]
}