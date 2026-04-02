from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (rag_summarize, get_weather, get_user_location, get_user_id,
                                     get_current_month, fill_context_for_report,memory_retrieve)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.logger_handler import logger
import uuid
from agent.tools.arxiv_tools import arxiv_tools
from agent.tools.weibo_hot_search_tool import weibo_hot_tools


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fill_context_for_report,memory_retrieve] + arxiv_tools + weibo_hot_tools,
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )
        # 初始化对话历史列表，每个对话都有独立的历史
        self.conversations = {}  # {conversation_id: history_list}
        self.current_conversation_id = "default"
        
        # 初始化默认对话
        self.conversations[self.current_conversation_id] = []
        
        # 初始化向量数据库连接，用于长期记忆存储
        self.long_term_memory_db = Chroma(
            collection_name=chroma_conf["memory_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf.get("memory_persist_directory", "memory_db")),
        )
        
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def execute_stream(self, query: str, conversation_id: str = None):
        if conversation_id is None:
            conversation_id = self.current_conversation_id
            
        # 确保对话存在
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # 将当前用户查询添加到对话历史
        self.conversations[conversation_id].append({
            "role": "user",
            "content": query
        })

        input_dict = {
            "messages": self.conversations[conversation_id]
        }

        # 第三个参数context就是上下文runtime中的信息，就是我们做提示词切换的标记
        full_response = ""
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                full_response += latest_message.content.strip() + "\n"
        
        # 将AI的回复也添加到对话历史中
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": full_response.strip()
        })
        
        # 流式返回响应
        for char in full_response:
            yield char

    def create_new_conversation(self, conversation_id: str = None):
        """创建新对话"""
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        self.conversations[conversation_id] = []
        self.current_conversation_id = conversation_id
        return conversation_id

    def switch_conversation(self, conversation_id: str):
        """切换到指定对话"""
        if conversation_id in self.conversations:
            self.current_conversation_id = conversation_id
            return True
        return False

    def get_current_conversation_id(self):
        """获取当前对话ID"""
        return self.current_conversation_id

    def get_conversation_history(self, conversation_id: str = None):
        """获取指定对话的历史，默认获取当前对话历史"""
        if conversation_id is None:
            conversation_id = self.current_conversation_id
            
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]
        return []

    def get_all_conversations(self):
        """获取所有对话的列表"""
        return list(self.conversations.keys())

    def get_conversation_summary(self, conversation_id: str = None):
        """获取对话摘要"""
        if conversation_id is None:
            conversation_id = self.current_conversation_id
            
        history = self.get_conversation_history(conversation_id)
        if not history:
            return "空对话"
        
        # 获取第一条用户消息作为摘要
        for msg in history:
            if msg["role"] == "user":
                return msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        return "对话开始"

    def delete_conversation(self, conversation_id: str):
        """删除指定对话"""
        if conversation_id in self.conversations and conversation_id != "default":
            del self.conversations[conversation_id]
            # 如果删除的是当前对话，则切换到默认对话
            if self.current_conversation_id == conversation_id:
                self.current_conversation_id = "default"
            return True
        return False

    def save_conversation_to_long_term_memory(self, conversation_id: str = None, title: str = ""):
        """
        将对话保存到长期记忆（向量数据库）
        """
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        history = self.get_conversation_history(conversation_id)
        if not history:
            return False, "对话历史为空，无法保存"
        
        try:
            # 将对话历史转换为文本格式
            conversation_text = f"对话标题: {title}\n\n"
            for msg in history:
                role = "用户" if msg["role"] == "user" else "助手"
                conversation_text += f"{role}: {msg['content']}\n\n"
            
            # 创建文档对象
            doc = Document(
                page_content=conversation_text,
                metadata={
                    "conversation_id": conversation_id,
                    "title": title or f"对话_{conversation_id}",
                    "source": "conversation_memory"
                }
            )
            
            # 分割文档
            split_docs = self.spliter.split_documents([doc])
            
            # 添加到向量数据库
            ids = self.long_term_memory_db.add_documents(split_docs)
            
            return True, f"成功将对话保存到长期记忆，创建了 {len(split_docs)} 个文档片段"
        
        except Exception as e:
            return False, f"保存到长期记忆失败: {str(e)}"

    def search_long_term_memory(self, query: str, k: int = 3):
        """
        从长期记忆中搜索相关信息
        """
        try:
            retriever = self.long_term_memory_db.as_retriever(search_kwargs={"k": k})
            results = retriever.invoke(query)
            return results
        except Exception as e:
            logger.error(f"从长期记忆搜索失败: {str(e)}")
            return []


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)