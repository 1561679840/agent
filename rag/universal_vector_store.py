from abc import ABC, abstractmethod
from langchain_core.documents import Document
from typing import List, Optional
from utils.config_handler import rag_conf


class VectorStoreInterface(ABC):
    """向量存储接口，定义所有向量数据库应实现的方法"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]):
        """添加文档"""
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """相似性搜索"""
        pass

    @abstractmethod
    def get_doc_count(self) -> int:
        """获取文档数量"""
        pass


class UniversalVectorStoreService(VectorStoreInterface):
    """统一向量存储服务，支持ChromaDB和Milvus"""
    
    def __init__(self, provider: str = None):
        # 从配置获取向量数据库提供商，如果没有指定则使用默认值
        self.provider = provider or rag_conf.get('vector_store_provider', 'chroma')
        
        if self.provider == 'milvus':
            from rag.milvus_vector_store import MilvusVectorStoreService
            self.service = MilvusVectorStoreService()
        elif self.provider == 'chroma':
            from rag.vector_store import VectorStoreService
            self.service = VectorStoreService()
        else:
            # 默认使用ChromaDB
            from rag.vector_store import VectorStoreService
            self.service = VectorStoreService()
    
    def add_documents(self, documents: List[Document]):
        """添加文档"""
        return self.service.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """相似性搜索"""
        return self.service.similarity_search(query, k)
    
    def get_doc_count(self) -> int:
        """获取文档数量"""
        return self.service.get_doc_count()
    
    def get_retriever(self, k: int = 3):
        """获取检索器"""
        if hasattr(self.service, 'get_retriever'):
            return self.service.get_retriever(k=k)
        else:
            # 如果底层服务不支持get_retriever，则创建一个包装
            return UniversalRetriever(self, k)


class UniversalRetriever:
    """通用检索器包装"""
    
    def __init__(self, vector_store: UniversalVectorStoreService, k: int = 3):
        self.vector_store = vector_store
        self.k = k
    
    def invoke(self, query: str) -> List[Document]:
        """调用检索"""
        return self.vector_store.similarity_search(query, k=self.k)