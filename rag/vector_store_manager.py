from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.logger_handler import logger
import os


class VectorStoreManager:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def get_all_documents(self):
        """
        获取向量库中所有的文档内容
        :return: 文档列表，每个元素包含id, content, metadata
        """
        try:
            # 获取集合对象
            collection = self.vector_store._collection
            # 正确的include参数：必须包含documents, metadatas, embeddings中的至少一个
            results = collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            documents_info = []
            for i in range(len(results['ids'])):
                doc_info = {
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i] if results['metadatas'] else {},
                    'embedding_length': len(results['embeddings'][i]) if results['embeddings'] is not None and i < len(results['embeddings']) else 0
                }
                documents_info.append(doc_info)
            
            return documents_info
        except Exception as e:
            logger.error(f"获取向量库文档失败：{str(e)}", exc_info=True)
            return []

    def delete_document_by_id(self, doc_id):
        """
        根据ID删除向量库中的文档
        :param doc_id: 要删除的文档ID
        :return: 删除是否成功
        """
        try:
            collection = self.vector_store._collection
            collection.delete(ids=[doc_id])
            logger.info(f"成功删除文档ID: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败，ID: {doc_id}, 错误: {str(e)}", exc_info=True)
            return False

    def delete_all_documents(self):
        """
        删除向量库中的所有文档
        :return: 删除是否成功
        """
        try:
            collection = self.vector_store._collection
            # 获取所有文档（这会同时返回ids）
            all_docs = collection.get(include=['documents'])
            if all_docs and 'ids' in all_docs and all_docs['ids']:
                collection.delete(ids=all_docs['ids'])
                logger.info(f"成功删除所有文档，共 {len(all_docs['ids'])} 个")
            return True
        except Exception as e:
            logger.error(f"清空向量库失败，错误: {str(e)}", exc_info=True)
            return False

    def get_document_count(self):
        """
        获取向量库中文档的数量
        :return: 文档数量
        """
        try:
            collection = self.vector_store._collection
            count = collection.count()
            return count
        except Exception as e:
            logger.error(f"获取文档数量失败：{str(e)}", exc_info=True)
            return 0

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    def load_document(self):
        """
        从数据文件夹内读取数据文件，转为向量存入向量库
        要计算文件的MD5做去重
        :return: None
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

                # 将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理好的文件的md5，避免下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path} 内容加载成功")
            except Exception as e:
                # exc_info为True会记录详细的报错堆栈，如果为False仅记录报错信息本身
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}", exc_info=True)
                continue