import os
import tempfile
from langchain_core.documents import Document
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, get_file_md5_hex
from utils.logger_handler import logger
from langchain_chroma import Chroma


class UploadVectorStoreService:
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

    def check_md5_hex(self, md5_for_check: str):
        """检查MD5是否已经存在于记录中"""
        if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
            # 创建文件
            open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
            return False  # md5 没处理过

        with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if line == md5_for_check:
                    return True  # md5 处理过

            return False  # md5 没处理过

    def save_md5_hex(self, md5_for_check: str):
        """保存MD5到记录文件"""
        with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
            f.write(md5_for_check + "\n")

    def get_file_documents(self, file_path: str):
        """根据文件扩展名选择合适的加载器"""
        if file_path.lower().endswith(".txt"):
            return txt_loader(file_path)

        if file_path.lower().endswith(".pdf"):
            return pdf_loader(file_path)

        return []

    def add_single_file(self, uploaded_file):
        """
        添加单个上传的文件到向量库
        :param uploaded_file: Streamlit上传的文件对象
        :return: 成功返回True，失败返回False
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name

            try:
                # 获取文件的MD5
                md5_hex = get_file_md5_hex(temp_file_path)

                if self.check_md5_hex(md5_hex):
                    logger.info(f"[上传知识库]{uploaded_file.name}内容已经存在知识库内，跳过")
                    return {"success": False, "message": f"文件 {uploaded_file.name} 已经存在于知识库中"}

                # 加载文档
                documents: list[Document] = self.get_file_documents(temp_file_path)

                if not documents:
                    logger.warning(f"[上传知识库]{uploaded_file.name}内没有有效文本内容，跳过")
                    return {"success": False, "message": f"文件 {uploaded_file.name} 中没有有效文本内容"}

                # 分片文档
                split_document: list[Document] = self.spliter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[上传知识库]{uploaded_file.name}分片后没有有效文本内容，跳过")
                    return {"success": False, "message": f"文件 {uploaded_file.name} 分片后没有有效文本内容"}

                # 将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理好的文件的md5，避免下次重复加载
                self.save_md5_hex(md5_hex)

                logger.info(f"[上传知识库]{uploaded_file.name} 内容加载成功")
                return {"success": True, "message": f"文件 {uploaded_file.name} 成功上传到知识库"}

            finally:
                # 删除临时文件
                os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"[上传知识库]{uploaded_file.name}上传失败：{str(e)}", exc_info=True)
            return {"success": False, "message": f"文件 {uploaded_file.name} 上传失败: {str(e)}"}

    def add_multiple_files(self, uploaded_files):
        """
        批量添加上传的文件到向量库
        :param uploaded_files: Streamlit上传的文件列表
        :return: 结果字典列表
        """
        results = []
        for uploaded_file in uploaded_files:
            result = self.add_single_file(uploaded_file)
            results.append(result)
        
        return results