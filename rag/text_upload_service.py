from langchain_core.documents import Document
from rag.universal_vector_store import UniversalVectorStoreService
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger_handler import logger
import hashlib


class TextUploadService:
    def __init__(self, provider=None):
        # 使用统一向量存储服务
        self.vector_store = UniversalVectorStoreService(provider=provider)

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def add_text(self, text_content: str, title: str = "Untitled"):
        """
        添加文本内容到向量库
        :param text_content: 要添加的文本内容
        :param title: 文档标题
        :return: 成功返回True，失败返回False
        """
        try:
            if not text_content or not text_content.strip():
                return {"success": False, "message": "文本内容不能为空"}
            
            # 创建文档对象
            doc = Document(
                page_content=text_content,
                metadata={
                    "source": f"text_input_{title}",
                    "title": title,
                    "type": "text_input"
                }
            )
            
            # 分割文档
            split_documents = self.spliter.split_documents([doc])
            
            # 添加到向量库
            ids = self.vector_store.add_documents(split_documents)
            
            logger.info(f"[文本上传]文本 '{title}' 成功上传到知识库")
            return {"success": True, "message": f"文本 '{title}' 成功上传到知识库，创建了 {len(split_documents)} 个文档片段"}
            
        except Exception as e:
            logger.error(f"[文本上传]文本上传失败：{str(e)}", exc_info=True)
            return {"success": False, "message": f"文本上传失败: {str(e)}"}