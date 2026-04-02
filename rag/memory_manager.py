from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.config_handler import chroma_conf
from model.factory import embed_model
from utils.path_tool import get_abs_path
from utils.logger_handler import logger
import os


class MemoryManager:
    def __init__(self):
        # 初始化记忆库
        self.memory_db = Chroma(
            collection_name=chroma_conf["memory_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf.get("memory_persist_directory", "memory_db")),
        )

    def get_all_memories(self):
        """
        获取记忆库中所有的记忆内容
        :return: 记忆列表，每个元素包含id, content, metadata
        """
        try:
            # 获取集合对象
            collection = self.memory_db._collection
            results = collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            memories_info = []
            for i in range(len(results['ids'])):
                mem_info = {
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i] if results['metadatas'] else {},
                    'embedding_length': len(results['embeddings'][i]) if results['embeddings'] is not None and len(results['embeddings']) > i else 0
                }
                memories_info.append(mem_info)
            
            return memories_info
        except Exception as e:
            logger.error(f"获取记忆库内容失败：{str(e)}", exc_info=True)
            return []

    def delete_memory_by_id(self, memory_id):
        """
        根据ID删除记忆库中的记忆
        :param memory_id: 要删除的记忆ID
        :return: 删除是否成功
        """
        try:
            collection = self.memory_db._collection
            collection.delete(ids=[memory_id])
            logger.info(f"成功删除记忆ID: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除记忆失败，ID: {memory_id}, 错误: {str(e)}", exc_info=True)
            return False

    def delete_all_memories(self):
        """
        删除记忆库中的所有记忆
        :return: 删除是否成功
        """
        try:
            collection = self.memory_db._collection
            # 获取所有记忆（这会同时返回ids）
            all_mems = collection.get(include=['documents'])
            if all_mems and 'ids' in all_mems and all_mems['ids']:
                collection.delete(ids=all_mems['ids'])
                logger.info(f"成功删除所有记忆，共 {len(all_mems['ids'])} 个")
            return True
        except Exception as e:
            logger.error(f"清空记忆库失败，错误: {str(e)}", exc_info=True)
            return False

    def get_memory_count(self):
        """
        获取记忆库中记忆的数量
        :return: 记忆数量
        """
        try:
            collection = self.memory_db._collection
            count = collection.count()
            return count
        except Exception as e:
            logger.error(f"获取记忆数量失败：{str(e)}", exc_info=True)
            return 0

    def search_memories(self, query: str, k: int = 3):
        """
        在记忆库中搜索相关内容
        :param query: 查询语句
        :param k: 返回结果数量
        :return: 搜索结果列表
        """
        try:
            retriever = self.memory_db.as_retriever(search_kwargs={"k": k})
            results = retriever.invoke(query)
            return results
        except Exception as e:
            logger.error(f"搜索记忆库失败：{str(e)}", exc_info=True)
            return []