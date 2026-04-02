"""Arxiv搜索和下载工具"""

import arxiv
from typing import List, Dict, Any
from langchain.tools import tool
import re
from utils.logger_handler import logger


@tool
def search_arxiv(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",
    sort_order: str = "descending"
) -> List[Dict[str, Any]]:
    """
    从Arxiv搜索学术论文
    
    Args:
        query: 搜索关键词或表达式
        max_results: 最大返回结果数，默认为5
        sort_by: 排序方式，可选 "relevance", "lastUpdatedDate", "submittedDate"
        sort_order: 排序顺序，可选 "ascending", "descending"
    
    Returns:
        包含论文信息的字典列表，每个字典包含以下键：
        - title: 标题
        - authors: 作者列表
        - summary: 摘要
        - published: 发表日期
        - updated: 更新日期
        - doi: DOI编号
        - pdf_url: PDF下载链接
        - journal_ref: 期刊引用信息
        - primary_category: 主要分类
        - categories: 所有分类
    
    Examples:
        >>> results = search_arxiv("machine learning", max_results=3)
        >>> print(results[0]['title'])
    """
    try:
        # 定义排序选项映射
        sort_mapping = {
            "relevance": arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": arxiv.SortCriterion.SubmittedDate
        }
        
        order_mapping = {
            "ascending": arxiv.SortOrder.Ascending,
            "descending": arxiv.SortOrder.Descending
        }
        
        # 验证参数
        if sort_by not in sort_mapping:
            sort_by = "relevance"
        if sort_order not in order_mapping:
            sort_order = "descending"
        
        # 执行搜索
        client = arxiv.Client(delay_seconds=5)
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_mapping[sort_by],
            sort_order=order_mapping[sort_order]
        )
        
        results = []
        for result in client.results(search):
            paper_info = {
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published": result.published.isoformat(),
                "updated": result.updated.isoformat(),
                "doi": result.doi,
                "pdf_url": result.pdf_url,
                "journal_ref": result.journal_ref,
                "primary_category": result.primary_category,
                "categories": result.categories
            }
            results.append(paper_info)
        
        logger.info(f"[Arxiv搜索] 搜索 '{query}'，找到 {len(results)} 篇论文")
        return results
        
    except Exception as e:
        logger.error(f"[Arxiv搜索] 搜索失败: {str(e)}", exc_info=True)
        return []


@tool
def download_arxiv_paper(
    paper_id: str,
    download_path: str = "./downloads/"
) -> Dict[str, Any]:
    """
    下载Arxiv论文PDF
    
    Args:
        paper_id: Arxiv论文ID (例如: "2103.04121" 或 "cs/0701008")
        download_path: 下载保存路径，默认为"./downloads/"
    
    Returns:
        包含下载结果信息的字典：
        - success: 是否下载成功
        - paper_id: 论文ID
        - title: 论文标题
        - download_path: 保存路径
        - file_path: 完整文件路径
        - error: 错误信息（如果有）
    
    Examples:
        >>> result = download_arxiv_paper("2103.04121")
        >>> print(result['success'])
    """
    try:
        import os
        from urllib.parse import urlparse
        import requests
        
        # 验证paper_id格式
        if not paper_id or not isinstance(paper_id, str):
            return {
                "success": False,
                "paper_id": paper_id,
                "error": "Invalid paper_id provided"
            }
        
        # 构建PDF URL
        if paper_id.startswith("http"):
            # 如果直接提供了URL
            pdf_url = paper_id
            paper_id = paper_id.split("/")[-1].replace(".pdf", "")
        else:
            # 构建标准arxiv URL
            pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        
        # 确保下载目录存在
        os.makedirs(download_path, exist_ok=True)
        
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 下载PDF文件
        response = requests.get(pdf_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                "success": False,
                "paper_id": paper_id,
                "error": f"HTTP {response.status_code}: Could not download paper"
            }
        
        # 获取论文标题（通过API获取元数据）
        search_result = list(arxiv.Search(id_list=[paper_id]).results())
        if search_result:
            title = search_result[0].title
        else:
            title = f"Paper_{paper_id}"
        
        # 清理标题以用作文件名
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]  # 限制文件名长度
        file_name = f"{clean_title}_{paper_id}.pdf"
        file_path = os.path.join(download_path, file_name)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        result = {
            "success": True,
            "paper_id": paper_id,
            "title": title,
            "download_path": download_path,
            "file_path": file_path
        }
        
        logger.info(f"[Arxiv下载] 论文 {paper_id} 已保存至 {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"[Arxiv下载] 下载失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "paper_id": paper_id,
            "error": str(e)
        }


@tool
def get_arxiv_paper_details(
    paper_id: str
) -> Dict[str, Any]:
    """
    获取Arxiv论文详细信息
    
    Args:
        paper_id: Arxiv论文ID (例如: "2103.04121" 或 "cs/0701008")
    
    Returns:
        包含论文详细信息的字典：
        - title: 标题
        - authors: 作者列表
        - summary: 摘要
        - published: 发表日期
        - updated: 更新日期
        - doi: DOI编号
        - pdf_url: PDF下载链接
        - journal_ref: 期刊引用信息
        - primary_category: 主要分类
        - categories: 所有分类
        - comment: 作者评论
        - error: 错误信息（如果有）
    
    Examples:
        >>> details = get_arxiv_paper_details("2103.04121")
        >>> print(details['title'])
    """
    try:
        # 搜索论文
        search = arxiv.Search(id_list=[paper_id])
        results = list(search.results())
        
        if not results:
            return {
                "error": f"Paper with ID {paper_id} not found"
            }
        
        result = results[0]
        
        paper_info = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary,
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "doi": result.doi,
            "pdf_url": result.pdf_url,
            "journal_ref": result.journal_ref,
            "primary_category": result.primary_category,
            "categories": result.categories,
            "comment": result.comment
        }
        
        logger.info(f"[Arxiv详情] 获取论文 {paper_id} 详情成功")
        return paper_info
        
    except Exception as e:
        logger.error(f"[Arxiv详情] 获取详情失败: {str(e)}", exc_info=True)
        return {
            "error": str(e)
        }


# 注册所有arxiv相关工具
arxiv_tools = [
    search_arxiv,
    download_arxiv_paper,
    get_arxiv_paper_details
]