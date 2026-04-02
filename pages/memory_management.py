import streamlit as st
from rag.memory_manager import MemoryManager
from utils.path_tool import get_abs_path
from utils.config_handler import chroma_conf

# 设置页面标题
st.set_page_config(
    page_title="记忆库管理 - AI智能助手",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 记忆库管理")
st.caption("查看、删除和管理长期记忆库中的对话内容")

st.divider()

# 初始化记忆库服务
if "memory_manager" not in st.session_state:
    st.session_state["memory_manager"] = MemoryManager()

# 侧边栏 - 管理操作
with st.sidebar:
    st.header("📋 记忆库操作")
    
    # 显示记忆库统计信息
    mem_count = st.session_state["memory_manager"].get_memory_count()
    st.metric(label="记忆片段数", value=mem_count)
    
    st.divider()
    
    # 删除操作
    st.subheader("🗑️ 删除操作")
    
    if st.button("🗑️ 删除全部记忆", type="secondary", use_container_width=True):
        with st.spinner("正在删除全部记忆..."):
            success = st.session_state["memory_manager"].delete_all_memories()
            if success:
                st.success("✅ 所有记忆已成功删除！")
                if "loaded_memory_docs" in st.session_state:
                    del st.session_state["loaded_memory_docs"]
                st.rerun()
            else:
                st.error("❌ 删除失败，请检查日志")

# 主页面内容
tab1, tab2 = st.tabs(["📖 查看记忆库内容", "🔍 搜索记忆"])

with tab1:
    st.subheader("📖 记忆库内容概览")
    
    total_mems = st.session_state["memory_manager"].get_memory_count()
    
    if total_mems == 0:
        st.info("🧠 记忆库中暂无任何记忆内容")
    else:
        st.info(f"🧠 记忆库中共有 {total_mems} 个记忆片段")
        
        # 获取所有记忆
        if st.button("🔄 刷新记忆列表"):
            with st.spinner("正在加载记忆库内容..."):
                docs = st.session_state["memory_manager"].get_all_memories()
                st.session_state["loaded_memory_docs"] = docs
        
        # 默认加载内容
        if "loaded_memory_docs" not in st.session_state:
            with st.spinner("正在加载记忆库内容..."):
                st.session_state["loaded_memory_docs"] = st.session_state["memory_manager"].get_all_memories()
        
        docs = st.session_state["loaded_memory_docs"]
        
        # 搜索框
        search_term = st.text_input("🔍 搜索记忆内容", placeholder="输入关键词搜索...")
        
        # 过滤记忆
        if search_term:
            filtered_docs = [doc for doc in docs if search_term.lower() in doc['content'].lower()]
            st.write(f"找到 {len(filtered_docs)} 个匹配的记忆片段")
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
        
        # 显示记忆列表
        for idx, doc in enumerate(current_docs):
            title = doc['metadata'].get('title', f"记忆_{doc['id'][:8]}...")
            with st.expander(f"🧠 记忆片段 #{start_idx + idx + 1}: {title}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text_area("内容预览:", value=doc['content'][:500] + ("..." if len(doc['content']) > 500 else ""), height=150, key=f"preview_mem_{doc['id']}")
                
                with col2:
                    st.write(f"**ID:** `{doc['id'][:8]}...`")
                    st.write(f"**长度:** {len(doc['content'])} 字符")
                    if 'conversation_id' in doc['metadata']:
                        st.write(f"**对话ID:** `{doc['metadata']['conversation_id'][:8]}...`")
                    if 'title' in doc['metadata']:
                        st.write(f"**标题:** {doc['metadata']['title']}")
                
                # 删除按钮
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"🗑️ 删除此记忆", key=f"delete_mem_{doc['id']}", type="secondary"):
                        with st.spinner("正在删除..."):
                            success = st.session_state["memory_manager"].delete_memory_by_id(doc['id'])
                            if success:
                                # 更新缓存
                                st.session_state["loaded_memory_docs"] = [d for d in st.session_state["loaded_memory_docs"] if d['id'] != doc['id']]
                                st.success(f"✅ 记忆片段 {doc['id'][:8]}... 已成功删除")
                                st.rerun()
                            else:
                                st.error("❌ 删除失败，请检查日志")
                with col_btn2:
                    # 复制ID功能
                    if st.button(f"📋 复制ID", key=f"copy_mem_{doc['id']}", type="secondary"):
                        st.code(doc['id'], language='text')
        
        # 批量删除功能
        if len(current_docs) > 0:
            st.subheader("📦 批量删除")
            selected_docs = st.multiselect(
                "选择要删除的记忆片段",
                options=[f"#{start_idx + idx + 1}: {doc['metadata'].get('title', doc['content'][:30] + '...')}" for idx, doc in enumerate(current_docs)],
                format_func=lambda x: x
            )
            
            if st.button("🗑️ 批量删除选中记忆"):
                if selected_docs:
                    with st.spinner("正在批量删除..."):
                        deleted_count = 0
                        for idx, doc in enumerate(current_docs):
                            display_option = f"#{start_idx + idx + 1}: {doc['metadata'].get('title', doc['content'][:30] + '...')}"
                            if display_option in selected_docs:
                                success = st.session_state["memory_manager"].delete_memory_by_id(doc['id'])
                                if success:
                                    deleted_count += 1
                        
                        if deleted_count > 0:
                            # 更新缓存
                            if "loaded_memory_docs" in st.session_state:
                                # 重新加载所有记忆
                                st.session_state["loaded_memory_docs"] = st.session_state["memory_manager"].get_all_memories()
                            st.success(f"✅ 成功删除 {deleted_count} 个记忆片段")
                            st.rerun()
                        else:
                            st.error("❌ 批量删除失败")
                else:
                    st.warning("请先选择要删除的记忆片段")

with tab2:
    st.subheader("🔍 搜索记忆内容")
    st.info("在记忆库中搜索相关内容，可用于查找之前的对话记录")
    
    search_query = st.text_input("输入搜索关键词", placeholder="例如：使用技巧、故障排除等...")
    
    if search_query:
        with st.spinner("正在搜索记忆库..."):
            results = st.session_state["memory_manager"].search_memories(search_query, k=10)
            
            if results:
                st.success(f"找到 {len(results)} 个相关记忆片段")
                
                for idx, doc in enumerate(results):
                    title = doc.metadata.get('title', f"相关记忆_{idx+1}")
                    with st.expander(f"🔍 相关记忆 {idx+1}: {title}", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write("**内容:**")
                            st.text_area("", value=doc.page_content[:1000] + ("..." if len(doc.page_content) > 1000 else ""), height=100, key=f"search_preview_{idx}")
                        
                        with col2:
                            if 'conversation_id' in doc.metadata:
                                st.write(f"**对话ID:** `{doc.metadata['conversation_id'][:8]}...`")
                            if 'title' in doc.metadata:
                                st.write(f"**标题:** {doc.metadata['title']}")
                            st.write(f"**相似度:** {doc.metadata.get('score', 'N/A')}")
            else:
                st.info("未找到相关记忆内容")

st.divider()

# 记忆库信息展示
with st.expander("ℹ️ 记忆库信息"):
    st.markdown(f"""
    ### 关于记忆库管理
    
    - **存储位置**: {get_abs_path(chroma_conf.get("memory_persist_directory", "memory_db"))}
    - **集合名称**: {chroma_conf["memory_name"]}
    - **用途**: 存储用户主动保存的重要对话记录
    
    ### 操作说明
    
    1. **查看内容**: 在"📖 查看记忆库内容"标签页中可以浏览所有已保存的记忆
    2. **删除记忆**: 
       - 单个删除：点击每个记忆旁边的"删除此记忆"按钮
       - 批量删除：在下方选择多个记忆后点击"批量删除选中记忆"
       - 全部删除：在侧边栏点击"删除全部记忆"
    3. **搜索记忆**: 在"🔍 搜索记忆"标签页中可以根据关键词搜索记忆内容
    """)