import streamlit as st

# 主页面 - 导航栏
st.set_page_config(
    page_title="AI智能助手",
    page_icon="🤖",
    layout="wide"
)

# 页面标题
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🤖 AI智能助手系统</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>一个功能强大的智能助手平台，为您提供全方位的支持服务</p>", unsafe_allow_html=True)

# 功能介绍卡片
st.markdown("### 🚀目录 ")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """<div style="border: 2px solid #1E88E5; border-radius: 10px; padding: 20px; margin: 10px; background-color: #E3F2FD;">
            <h3 style="color: #1E88E5; text-align: center;">💬 智能问答</h3>
            <p style="text-align: center;">与AI进行自然对话，获取即时解答</p>
            <div style="text-align: center;">
                <span style="display: inline-block; background-color: #2196F3; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;">
                    实时互动
                </span>
            </div>
        </div>""", unsafe_allow_html=True)
    

with col2:
    st.markdown(
        """<div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 20px; margin: 10px; background-color: #E8F5E9;">
            <h3 style="color: #4CAF50; text-align: center;">📚 知识上传</h3>
            <p style="text-align: center;">上传文档到知识库，让机器人学习更多专业知识</p>
            <div style="text-align: center;">
                <span style="display: inline-block; background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;">
                    知识扩展
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(
        """<div style="border: 2px solid #FF9800; border-radius: 10px; padding: 20px; margin: 10px; background-color: #FFF3E0;">
            <h3 style="color: #FF9800; text-align: center;">🗂️ 知识库管理</h3>
            <p style="text-align: center;">查看、删除和管理知识库中的文档内容</p>
            <div style="text-align: center;">
                <span style="display: inline-block; background-color: #FF9800; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;">
                    内容管理
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(
        """<div style="border: 2px solid #9C27B0; border-radius: 10px; padding: 20px; margin: 10px; background-color: #F3E5F5;">
            <h3 style="color: #9C27B0; text-align: center;">🧠 记忆库管理</h3>
            <p style="text-align: center;">查看、删除和管理长期记忆库中的对话内容</p>
            <div style="text-align: center;">
                <span style="display: inline-block; background-color: #9C27B0; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;">
                    智能记忆
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# 欢迎信息卡片
st.markdown("""<div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 10px; margin-bottom: 30px;'>
<h3 style='text-align: center; color: #2C3E50;'>欢迎使用AI智能助手系统</h3>
<p style='text-align: center; color: #34495E;'>请选择您需要的服务：</p>
<ul style='color: #34495E;'>
<li><strong>智能问答</strong>: 与AI进行对话，获取问题解答</li>
<li><strong>知识库管理</strong>: 上传、查看和管理知识库中的文档</li>
<li><strong>知识库文件上传</strong>: 上传您的文档到知识库，丰富知识储备</li>
</ul>
</div>""", unsafe_allow_html=True)

st.divider()