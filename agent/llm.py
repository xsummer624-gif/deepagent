from dotenv import load_dotenv,find_dotenv
import os
from langchain.chat_models import init_chat_model

# find_dotenv()确保找到.env 递归查询当前项目文件
load_dotenv(find_dotenv())

model = init_chat_model(
    model=os.getenv("DEEPSEEK_MODEL_R"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
