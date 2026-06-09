from ragflow_sdk import RAGFlow
from ragflow.rag_config import _load_ragflow_env
import os

# 创建一个ragflow的客户端
api_key,base_url = _load_ragflow_env()
ragflow_client = RAGFlow(api_key=api_key,base_url=base_url)

# 1.查询现在知识库中有哪些聊天助手和对应知识库的信息
def get_assistant_list():
    #1.创建ragflow客户端
    #2.ragflow客户端查询所有的聊天助手
    chat_list = ragflow_client.list_chats()
    #3.查询聊天助手的知识库信息
    count_chat_info = ""
    for chat in chat_list:
        dataset_names = []
        dataset_list = chat.datasets
        if dataset_list and isinstance(dataset_list, list):
            for dataset in dataset_list:
                print(dataset)
                dataset_names.append(dataset['name'])
        count_chat_info += f"助手名称{chat.name};功能介绍{chat.description};关联知识库{','.join(dataset_names)}\n"
    return count_chat_info
# 2.对某个助手进行提问
def ask_question(chat_name,question):
    """
    向某个助手进行提问：1.创建一个会话 2.提问 3.关闭会话
    :param chat_name: 助手名字
    :param question: 问题
    :return:返回提问结果
    """
    #1.创建ragflow客户端
    #2.查询对应name的chat
    chats = ragflow_client.list_chats(name=chat_name)
    use_chat = chats[0]
    #3.chat上一个创建会话
    session = use_chat.create_session(name="temp_session_ask")
    #4.使用会话进项提问
    #返回的提问结果是流式
    response = session.ask(question,stream=True)
    #接收总结果
    result = ""
    #流的每一部分的对象 part
    for part in response:
        #数据存在对象中content
        result = part.content
    #5.关闭提问会话
    use_chat.delete_session(ids=[session.id])
    #6.返回结果
    return result
if __name__ == '__main__':
    print(get_assistant_list())
    print(ask_question("法律援助助手","你好啊"))