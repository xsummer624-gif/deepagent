from agent.prompts import sub_agents_content
from tools.tavily_tool import internet_search

network_search_agent = {
    "name": sub_agents_content["tavily"].get("name", ""),
    "description": sub_agents_content["tavily"].get("description", ""),
    "system_prompt": sub_agents_content["tavily"].get("system_prompt", ""),
    "tools": [internet_search]
}

