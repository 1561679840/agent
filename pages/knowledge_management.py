import streamlit as st
from rag.vector_store_manager import VectorStoreManager
import os

# 设置页面标题
st.set_page_config(
    page_title="知识库管理 - AI智能助手",
    page_icon="🗂️",
    layout="wide"
)

st.title("🗂️ 知识库管理")
st.caption("查看、删除和管理知识库中的文档内容")

st.divider()

# 初始化上传服务
if "vector_store_manager" not in st.session_state:
    st.session_state["vector_store_manager"] = VectorStoreManager()

# 侧边栏 - 管理操作
with st.sidebar:
    st.header("📋 管理操作")
    
    # 显示文档统计信息
    doc_count = st.session_state["vector_store_manager"].get_document_count()
    st.metric(label="总文档数", value=doc_count)
    
    st.divider()
    
    # 删除操作
    st.subheader("🗑️ 删除操作")
    
    if st.button("🗑️ 删除全部文档", type="secondary", use_container_width=True):
        with st.spinner("正在删除全部文档..."):
            success = st.session_state["vector_store_manager"].delete_all_documents()
            if success:
                st.success("✅ 所有文档已成功删除！")
                if "loaded_docs" in st.session_state:
                    del st.session_state["loaded_docs"]
                st.rerun()
            else:
                st.error("❌ 删除失败，请检查日志")
    
    st.divider()
    
    # 重新加载知识库
    st.subheader("🔄 知识库同步")
    if st.button("🔄 从数据文件夹重新加载", type="primary", use_container_width=True):
        with st.spinner("正在重新加载知识库..."):
            try:
                st.session_state["vector_store_manager"].load_document()
                st.success("✅ 知识库重新加载完成！")
                if "loaded_docs" in st.session_state:
                    del st.session_state["loaded_docs"]
                st.rerun()
            except Exception as e:
                st.error(f"❌ 重新加载失败: {str(e)}")

# 主页面内容
tab1, tab2 = st.tabs(["📖 查看知识库内容", "📥 上传新文档"])

with tab1:
    st.subheader("📖 知识库内容概览")
    
    # 获取文档总数
    total_docs = st.session_state["vector_store_manager"].get_document_count()
    
    if total_docs == 0:
        st.info("📚 知识库中暂无任何文档内容")
    else:
        st.info(f"📚 知识库中共有 {total_docs} 个文档片段")
        
        # 获取所有文档
        if st.button("🔄 刷新内容列表"):
            with st.spinner("正在加载知识库内容..."):
                docs = st.session_state["vector_store_manager"].get_all_documents()
                st.session_state["loaded_docs"] = docs
        
        # 默认加载内容
        if "loaded_docs" not in st.session_state:
            with st.spinner("正在加载知识库内容..."):
                st.session_state["loaded_docs"] = st.session_state["vector_store_manager"].get_all_documents()
        
        docs = st.session_state["loaded_docs"]
        
        # 搜索框
        search_term = st.text_input("🔍 搜索文档内容", placeholder="输入关键词搜索...")
        
        # 过滤文档
        if search_term:
            filtered_docs = [doc for doc in docs if search_term.lower() in doc['content'].lower()]
            st.write(f"找到 {len(filtered_docs)} 个匹配的文档片段")
        else:
            filtered_docs = docs
        
        # 分页显示
        items_per_page = 10
        total_pages = (len(filtered_docs) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            page_number = st.selectbox("选择页数", options=list(range(1, total_pages + 1)), format_func=lambda x: f"第 {x} 页")
            start_idx = (page_number - 1) * items_per_page
            end_idx = start_idx + items_per_page
            current_docs = filtered_docs[start_idx:end_idx]
        else:
            current_docs = filtered_docs
            start_idx = 0  # 确保start_idx被定义
        
        # 显示文档列表
        for idx, doc in enumerate(current_docs):
            with st.expander(f"📄 片段 #{start_idx + idx + 1}: {doc['content'][:50]}{'...' if len(doc['content']) > 50 else ''}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text_area("内容预览:", value=doc['content'][:500] + ("..." if len(doc['content']) > 500 else ""), height=100, key=f"preview_{doc['id']}")
                
                with col2:
                    st.write(f"**ID:** `{doc['id'][:8]}...`")
                    st.write(f"**长度:** {len(doc['content'])} 字符")
                    if 'source' in doc['metadata']:
                        st.write(f"**来源:** {os.path.basename(doc['metadata']['source'])}")
                
                # 删除按钮
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"🗑️ 删除此片段", key=f"delete_{doc['id']}", type="secondary"):
                        with st.spinner("正在删除..."):
                            success = st.session_state["vector_store_manager"].delete_document_by_id(doc['id'])
                            if success:
                                # 更新缓存
                                st.session_state["loaded_docs"] = [d for d in st.session_state["loaded_docs"] if d['id'] != doc['id']]
                                st.success(f"✅ 片段 {doc['id'][:8]}... 已成功删除")
                                st.rerun()
                            else:
                                st.error("❌ 删除失败，请检查日志")
                with col_btn2:
                    # 复制ID功能
                    if st.button(f"📋 复制ID", key=f"copy_{doc['id']}", type="secondary"):
                        st.code(doc['id'], language='text')
        
        # 批量删除功能
        if len(current_docs) > 0:
            st.subheader("📦 批量删除")
            selected_docs = st.multiselect(
                "选择要删除的文档片段",
                options=[f"#{start_idx + idx + 1}: {doc['content'][:30]}{'...' if len(doc['content']) > 30 else ''}" for idx, doc in enumerate(current_docs)],
                format_func=lambda x: x
            )
            
            if st.button("🗑️ 批量删除选中文档"):
                if selected_docs:
                    with st.spinner("正在批量删除..."):
                        deleted_count = 0
                        for idx, doc in enumerate(current_docs):
                            display_option = f"#{start_idx + idx + 1}: {doc['content'][:30]}{'...' if len(doc['content']) > 30 else ''}"
                            if display_option in selected_docs:
                                success = st.session_state["vector_store_manager"].delete_document_by_id(doc['id'])
                                if success:
                                    deleted_count += 1
                        
                        if deleted_count > 0:
                            # 更新缓存
                            if "loaded_docs" in st.session_state:
                                # 重新加载所有文档
                                st.session_state["loaded_docs"] = st.session_state["vector_store_manager"].get_all_documents()
                            st.success(f"✅ 成功删除 {deleted_count} 个文档片段")
                            st.rerun()
                        else:
                            st.error("❌ 批量删除失败")
                else:
                    st.warning("请先选择要删除的文档片段")

with tab2:
    st.subheader("📥 上传新文档到知识库")
    st.info("支持PDF和TXT格式的文档，系统会自动提取文档内容并将其向量化存储")
    
    uploaded_files = st.file_uploader(
        "选择要上传到知识库的文件", 
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="您可以一次选择多个文件进行上传"
    )
    
    if uploaded_files:
        st.write(f"已选择 {len(uploaded_files)} 个文件:")
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.type}, {(file.size/1024):.2f} KB)")
        
        if st.button("📤 上传到知识库", type="primary"):
            with st.spinner("正在上传文件到知识库..."):
                # 这里需要创建一个临时的上传服务，因为我们已经有了VectorStoreManager
                from rag.upload_vector_store import UploadVectorStoreService
                upload_service = UploadVectorStoreService()
                
                results = upload_service.add_multiple_files(uploaded_files)
                
                success_count = 0
                for result in results:
                    if result["success"]:
                        success_count += 1
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
                
                if success_count > 0:
                    st.success(f"✅ 成功上传 {success_count} 个文件到知识库！")
                    # 清除缓存以便刷新内容
                    if "loaded_docs" in st.session_state:
                        del st.session_state["loaded_docs"]
                    st.rerun()
                else:
                    st.warning("⚠️ 没有文件被成功上传")

st.divider()

# 知识库信息展示
with st.expander("ℹ️ 知识库信息"):
    st.markdown(f"""
    ### 关于知识库管理
    
    - **支持格式**: PDF, TXT
    - **存储位置**: 本地Chroma数据库
    - **去重机制**: 基于文件MD5值，避免重复上传相同内容
    - **文档处理**: 自动分块处理，便于向量检索
    
    ### 操作说明
    
    1. **查看内容**: 在"📖 查看知识库内容"标签页中可以浏览所有已存储的文档
    2. **删除文档**: 
       - 单个删除：点击每个文档旁边的"删除此片段"按钮
       - 批量删除：在下方选择多个文档后点击"批量删除选中文档"
       - 全部删除：在侧边栏点击"删除全部文档"
    3. **上传文档**: 在"📥 上传新文档"标签页中可以添加新文档
    4. **重新加载**: 可以从数据文件夹重新加载所有文档
    """)