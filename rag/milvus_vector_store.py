from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from langchain_core.documents import Document
from utils.config_handler import chroma_conf, rag_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.logger_handler import logger
import os
import uuid
from typing import List, Optional


class MilvusVectorStoreService:
    def __init__(self, collection_name: str = None):
        # 从配置文件获取Milvus连接信息
        milvus_conf = getattr(rag_conf, 'milvus', {
            'host': 'localhost',
            'port': 19530,
            'user': '',
            'password': '',
            'secure': False
        })
        
        self.host = milvus_conf.get('host', 'localhost')
        self.port = milvus_conf.get('port', 19530)
        self.collection_name = collection_name or milvus_conf.get('collection_name', 'default_collection')
        
        # 连接到Milvus
        connections.connect(alias="default", host=self.host, port=self.port)
        
        # 初始化文本分割器
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )
        
        # 创建集合（如果不存在）
        self.create_collection_if_not_exists()

    def create_collection_if_not_exists(self):
        """创建Milvus集合（如果不存在）"""
        if utility.has_collection(self.collection_name):
            logger.info(f"集合 {self.collection_name} 已存在")
            return

        # 获取嵌入维度（通过临时嵌入一个句子来确定）
        test_embedding = embed_model.embed_query("test")
        embedding_dim = len(test_embedding)

        # 定义集合的schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=65535),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]

        schema = CollectionSchema(fields, description="Document collection for RAG")
        
        # 创建集合
        collection = Collection(name=self.collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        logger.info(f"创建了Milvus集合: {self.collection_name}")

    def add_documents(self, documents: List[Document]):
        """添加文档到Milvus"""
        try:
            collection = Collection(self.collection_name)
            collection.load()  # 加载集合到内存

            # 准备插入的数据
            ids = []
            contents = []
            embeddings = []
            sources = []
            metadatas = []

            for doc in documents:
                doc_id = str(uuid.uuid4())
                content = doc.page_content
                embedding = embed_model.embed_query(content)
                source = doc.metadata.get('source', '')
                metadata = doc.metadata

                ids.append(doc_id)
                contents.append(content)
                embeddings.append(embedding)
                sources.append(source)
                metadatas.append(metadata)

            # 插入数据
            entities = [
                ids,
                contents,
                embeddings,
                sources,
                metadatas
            ]

            insert_result = collection.insert(entities)
            collection.flush()  # 确保数据写入
            
            logger.info(f"成功添加 {len(documents)} 个文档到Milvus集合 {self.collection_name}")
            return insert_result.primary_keys

        except Exception as e:
            logger.error(f"添加文档到Milvus失败: {str(e)}", exc_info=True)
            return []

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """根据查询进行相似性搜索"""
        try:
            collection = Collection(self.collection_name)
            collection.load()  # 加载集合到内存

            # 生成查询向量
            query_embedding = embed_model.embed_query(query)

            # 搜索参数
            search_params = {
                "data": [query_embedding],
                "anns_field": "embedding",
                "param": {"metric_type": "COSINE", "params": {"nprobe": 10}},
                "limit": k,
                "output_fields": ["content", "source", "metadata"],
            }

            results = collection.search(**search_params)

            # 构造返回的Document对象
            documents = []
            for hit in results[0]:  # results[0] 包含第一个查询（我们只有一个）的结果
                doc = Document(
                    page_content=hit.entity.get('content'),
                    metadata={
                        'id': hit.id,
                        'source': hit.entity.get('source'),
                        'score': hit.distance,
                        **hit.entity.get('metadata', {})
                    }
                )
                documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"Milvus相似性搜索失败: {str(e)}", exc_info=True)
            return []

    def delete_collection(self):
        """删除集合"""
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            logger.info(f"已删除Milvus集合: {self.collection_name}")

    def get_doc_count(self):
        """获取集合中文档数量"""
        try:
            collection = Collection(self.collection_name)
            return collection.num_entities
        except Exception as e:
            logger.error(f"获取文档数量失败: {str(e)}", exc_info=True)
            return 0

    def load_document(self):
        """
        从数据文件夹内读取数据文件，转为向量存入Milvus
        """
        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                # 创建文件
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
                return False            # md5 没处理过

            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_hex:
                        return True     # md5 处理过

                return False            # md5 没处理过

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_hex + "\n")

        def get_file_documents(read_path: str):
            if read_path.endswith(".txt"):
                return txt_loader(read_path)

            if read_path.endswith(".pdf"):
                return pdf_loader(read_path)

            return []

        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )

        for path in allowed_files_path:
            # 获取文件的MD5
            md5_hex = get_file_md5_hex(path)

            if check_md5_hex(md5_hex):
                logger.info(f"[加载知识库]{path}内容已经存在知识库内，跳过")
                continue

            try:
                documents: list[Document] = get_file_documents(path)

                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本内容，跳过")
                    continue

                split_document: list[Document] = self.spliter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue

                # 将内容存入Milvus
                self.add_documents(split_document)

                # 记录这个已经处理好的文件的md5，避免下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path} 内容加载成功")
            except Exception as e:
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}", exc_info=True)
                continue