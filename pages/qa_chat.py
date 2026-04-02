import time
import streamlit as st
from agent.react_agent import ReactAgent

# 设置页面标题
st.set_page_config(
    page_title="智能问答 - AI智能助手",
    page_icon="💬",
    layout="wide"
)

# 页面标题
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>💬 智能问答</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>与AI进行自然对话，获取专业解答和个性化服务</p>", unsafe_allow_html=True)

# 添加对话控制按钮
with st.sidebar:
    st.header("对话管理")
    
    # 创建新对话按钮
    if st.button("🆕 新建对话", use_container_width=True, type="primary"):
        new_conv_id = st.session_state["agent"].create_new_conversation()
        st.session_state["current_conversation_id"] = new_conv_id
        st.session_state["message"] = []
    
    st.divider()
    
    # 显示当前对话信息
    if "agent" in st.session_state:
        current_conv_id = st.session_state["agent"].get_current_conversation_id()
        st.metric("当前对话ID", current_conv_id[:12] + "..." if len(current_conv_id) > 12 else current_conv_id)
        
        history_length = len(st.session_state["agent"].get_conversation_history())
        st.metric("当前对话轮数", history_length)
    
    st.divider()
    
    # 长期记忆功能
    st.subheader("🧠 长期记忆")
    
    # 对话标题输入
    memory_title = st.text_input("记忆标题", placeholder="为这段对话添加一个标题...")
    
    # 保存到长期记忆按钮
    if st.button("💾 保存到长期记忆", use_container_width=True):
        if "agent" in st.session_state:
            success, message = st.session_state["agent"].save_conversation_to_long_term_memory(
                title=memory_title
            )
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("没有当前对话可以保存")
    
    st.divider()
    
    # 显示对话列表
    st.subheader("历史对话")
    if "agent" in st.session_state:
        all_conversations = st.session_state["agent"].get_all_conversations()
        
        # 为每个对话创建一个选择按钮
        for conv_id in all_conversations:
            if conv_id != "default" or len(st.session_state["agent"].get_conversation_history(conv_id)) > 0:  # 只显示非空的默认对话
                conv_summary = st.session_state["agent"].get_conversation_summary(conv_id)
                # 使用对话ID的简短版本作为标签
                short_id = conv_id[:8] + "..." if len(conv_id) > 8 else conv_id
                button_label = f"📋 {short_id}: {conv_summary}"
                
                if st.button(button_label, key=f"switch_conv_{conv_id}", use_container_width=True):
                    st.session_state["agent"].switch_conversation(conv_id)
                    st.session_state["current_conversation_id"] = conv_id
                    # 同步消息历史
                    st.session_state["message"] = st.session_state["agent"].get_conversation_history(conv_id)

st.divider()

# 初始化session状态
if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"] = []

# 确保当前对话ID已设置
if "current_conversation_id" not in st.session_state:
    st.session_state["current_conversation_id"] = st.session_state["agent"].get_current_conversation_id()

# 同步聊天历史与ReactAgent的当前对话历史
current_history = st.session_state["agent"].get_conversation_history()
if current_history != st.session_state["message"]:
    st.session_state["message"] = current_history

# 显示聊天历史
for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 用户输入提示词
prompt = st.chat_input("请输入您的问题...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages = []
    with st.spinner("智能客服思考中..."):
        # 使用当前对话ID执行查询
        res_stream = st.session_state["agent"].execute_stream(
            prompt, 
            conversation_id=st.session_state["current_conversation_id"]
        )

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)

                for char in chunk:
                    time.sleep(0.01)
                    yield char

        st.chat_message("assistant").write_stream(capture(res_stream, response_messages))
        # 更新消息历史
        st.session_state["message"] = st.session_state["agent"].get_conversation_history(
            st.session_state["current_conversation_id"]
        )