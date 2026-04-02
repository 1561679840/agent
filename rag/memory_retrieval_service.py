"""
记忆检索服务类：从记忆库中检索相关信息
"""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_core.prompts import PromptTemplate
from model.factory import chat_model
from langchain_chroma import Chroma
from utils.path_tool import get_abs_path


def print_prompt(prompt):
    print("="*20)
    print(prompt.to_string())
    print("="*20)
    return prompt


class MemoryRetrievalService(object):
    def __init__(self):
        # 使用记忆库进行检索
        self.memory_db = Chroma(
            collection_name=chroma_conf["memory_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf.get("memory_persist_directory", "memory_db")),
        )
        self.retriever = self.memory_db.as_retriever()
        self.prompt_template = PromptTemplate.from_template(
            "根据以下记忆库中的参考资料回答用户的问题：\n\n{context}\n\n用户问题：{input}\n\n请基于参考资料提供准确的回答，如果参考资料中没有相关信息，请说明没有找到相关内容。"
        )
        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        chain = self.prompt_template | print_prompt | self.model | StrOutputParser()
        return chain

    def retrieve_memory_docs(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)

    def memory_retrieve_and_answer(self, query: str) -> str:
        context_docs = self.retrieve_memory_docs(query)

        context = ""
        counter = 0
        for doc in context_docs:
            counter += 1
            context += f"【记忆资料{counter}】: 记忆内容：{doc.page_content} | 记忆元数据：{doc.metadata}\n"

        return self.chain.invoke(
            {
                "input": query,
                "context": context,
            }
        )