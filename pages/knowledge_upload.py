import streamlit as st
from rag.universal_vector_store import UniversalVectorStoreService
from rag.text_upload_service import TextUploadService
from utils.config_handler import rag_conf

# 设置页面标题
st.set_page_config(
    page_title="知识库管理 - AI智能助手",
    page_icon="📚",
    layout="wide"
)

st.title("📚 知识库管理")
st.caption("上传文档到知识库，让AI学习更多专业知识")

st.divider()

# 初始化上传服务
if "upload_service" not in st.session_state:
    # 从配置中获取向量数据库提供商
    provider = rag_conf.get('vector_store_provider', 'chroma')
    st.session_state["upload_service"] = UniversalVectorStoreService(provider=provider)

if "text_upload_service" not in st.session_state:
    # 从配置中获取向量数据库提供商
    provider = rag_conf.get('vector_store_provider', 'chroma')
    st.session_state["text_upload_service"] = TextUploadService(provider=provider)

# 选项卡界面
tab1, tab2 = st.tabs(["📄 文件上传", "📝 文本输入"])

with tab1:
    st.subheader("上传文档到知识库")
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
        
        if st.button("上传到知识库", type="primary", key="file_upload_btn"):
            with st.spinner("正在上传文件到知识库..."):
                # 需要使用UploadVectorStoreService来处理文件上传
                from rag.upload_vector_store import UploadVectorStoreService
                provider = rag_conf.get('vector_store_provider', 'chroma')
                file_upload_service = UploadVectorStoreService(provider=provider)
                
                results = file_upload_service.add_multiple_files(uploaded_files)
                
                success_count = 0
                for result in results:
                    if result["success"]:
                        success_count += 1
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
                
                if success_count > 0:
                    st.success(f"✅ 成功上传 {success_count} 个文件到知识库！")
                    st.balloons()
                else:
                    st.warning("⚠️ 没有文件被成功上传")

with tab2:
    st.subheader("直接输入文本到知识库")
    st.info("在下方输入框中输入文本内容，系统会将其向量化并存储到知识库中")
    
    # 文本输入区域
    text_input = st.text_area(
        "输入要上传到知识库的文本内容", 
        height=200,
        placeholder="在这里输入您想要添加到知识库的文本内容..."
    )
    
    # 文档标题输入
    title_input = st.text_input(
        "文档标题", 
        placeholder="为这段文本输入一个标题（可选）",
        value="未命名文本"
    )
    
    if st.button("保存文本到知识库", type="primary"):
        if not text_input or not text_input.strip():
            st.warning("请输入要上传的文本内容")
        else:
            with st.spinner("正在处理文本并上传到知识库..."):
                result = st.session_state["text_upload_service"].add_text(text_input, title_input)
                
                if result["success"]:
                    st.success(result["message"])
                    st.balloons()
                else:
                    st.error(result["message"])

st.divider()

# 知识库信息展示
st.subheader("知识库信息")
st.info("上传的文档将被处理并存储在向量数据库中，AI可以在回答问题时引用这些知识。")

with st.expander("查看知识库详情"):
    st.markdown("""
    - **支持格式**: 
      - 文件上传: PDF, TXT
      - 文本输入: 任意文本内容
    - **去重机制**: 基于内容MD5值，避免重复上传相同内容
    - **文档处理**: 自动分块处理，便于向量检索
    - **存储位置**: 本地数据库（当前使用 {}）
    """.format(rag_conf.get('vector_store_provider', 'chroma')))