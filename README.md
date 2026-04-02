# 智能AI助手 🤖

> 基于 LangChain ReAct Agent + RAG + Streamlit 的智能AI助手系统

---
# 使用必看
请务必安装好相关配置环境，其中config/agent.yml文件中的gaodekey需要改为实际申请的高德key(也可以根据个人需要更改为更加隐式的办法)

## 📖 项目简介

系统以 Streamlit 构建轻量级前端网页，后端基于 LangChain 搭建 ReAct（Reasoning + Acting）Agent，整合以下核心能力：

- **RAG 增强检索**：可上传文档向量化存储，AI 回答时优先检索知识库，确保答案准确可靠。
- **高德 MCP 服务**：调用高德地图 API 实时获取用户定位与天气信息。
- **总结汇报模式**：中间件通过识别特定意图，动态切换系统提示词，自动生成使用情况报告（Markdown 格式）。
- **多轮工具调用**：Agent 可自主规划并多轮调用所配备的工具，直至满足用户需求。
- **流式响应**：最终结果在网页端以逐字流式方式呈现，提升交互体验。
- **完善的日志与历史**：配备结构化日志（文件 + 控制台）与对话历史记录。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **LLM** | 阿里云通义千问 `qwen3-max`（通过 `ChatTongyi`） 本地Ollama模型  OpenAI API |
| **Embedding** | 阿里云 DashScope `text-embedding-v4` 本地Ollama模型|
| **向量数据库** | Chroma（本地持久化） |
| **Agent 框架** | LangChain ReAct Agent + LangGraph |
| **前端** | Streamlit Web 界面，支持对话历史,文档上传,知识库片段查看删除,对话历史向量化入库|
| **外部服务** | 高德地图 REST API（天气、IP 定位） |
| **动态提示词** | 中间件根据上下文信号量自动切换 System Prompt |
| **去重机制** | MD5 哈希追踪已处理文档，避免重复入库 |
| **日志** | 按天分文件，同时输出到控制台与文件 |

---

## 📂 目录结构

```
zhisaotong-Agent/
├── app.py                        # Streamlit 前端入口
├── agent/
│   ├── react_agent.py            # ReAct Agent 核心逻辑
│   └── tools/
│       ├── agent_tools.py        # 工具函数定义
│       └── middleware.py         # Agent 中间件
        └── arxiv_tools.py        # 我添加的Arxiv 工具
        └── weibo_tools.py         # 我添加的微博API工具
├── rag/
│   ├── rag_service.py            # RAG 检索摘要服务
│   └── vector_store.py           # Chroma 向量库管理
    └── memory_manager.py           # 我添加的对话历史管理器
    └──=memory_retrieval_service.py       # 我添加的对话历史存储
    └── vector_store_memory.py           # 我添加的知识库管理(查看+删除)

├── model/
│   └── factory.py                # 模型工厂（LLM + Embedding）
├── utils/
│   ├── config_handler.py         # YAML 配置加载器
│   ├── logger_handler.py         # 日志工具
│   ├── prompt_loader.py          # 提示词加载器
│   ├── file_handler.py           # 文档加载（PDF/TXT）
│   └── path_tool.py              # 路径工具
├── config/
│   ├── agent.yml                 # Agent 配置（高德 API Key 等）
│   ├── rag.yml                   # 模型名称配置
│   ├── chroma.yml                # 向量库配置
│   └── prompts.yml               # 提示词文件路径
├── prompts/
│   ├── main_prompt.txt           # 主 ReAct 提示词
│   ├── rag_summarize.txt         # RAG 摘要提示词
│   └── report_prompt.txt         # 报告生成提示词
├── chroma_db/                    # Chroma 持久化目录（自动生成）
├── logs/                         # 日志文件目录（自动生成）
└── md5.text                      # 文档 MD5 去重记录
└── pages/                        # 我添加的前端页面

```

---

## 📦 环境依赖

### Python 版本

建议使用 **Python 3.10+**（代码中使用了 `tuple[str, str]` 等 3.10+ 类型注解语法）。

### 主要依赖包

| 包名 | 用途 |
|------|------|
| `streamlit` | 前端 Web 框架 |
| `langchain` | Agent / Chain / Tool 框架 |
| `langchain-core` | LangChain 核心抽象 |
| `langchain-community` | 通义千问、DashScope Embedding 等集成 |
| `langgraph` | 基于图的 Agent 执行引擎（含 `Runtime`） |
| `langchain-chroma` | LangChain 与 Chroma 向量库集成 |
| `chromadb` | Chroma 向量数据库 |
| `dashscope` | 阿里云 DashScope SDK（Embedding / LLM） |
| `pypdf` / `pypdf2` | PDF 文档加载 |
| `pyyaml` | YAML 配置文件解析 |

### 安装依赖

```bash
pip install streamlit langchain langchain-core langchain-community langgraph \
            langchain-chroma chromadb dashscope pypdf pyyaml
```


---

## ⚙️ 配置说明

### 1. 阿里云 API Key

本项目使用阿里云通义千问大模型和 DashScope Embedding，需要配置系统环境变量：

```bash
OPENAI_API_KEY="your_open_api_key"
```

> 可在 [阿里云百炼平台](https://bailian.console.aliyun.com/) 获取 API Key。

### 2. 高德地图 API Key

编辑 `config/agent.yml`，将 `gaodekey` 替换为你的高德地图 Web 服务 API Key：

```yaml
# config/agent.yml
external_data_path: data/external/records.csv
gaodekey: 你的高德key!        # ← 替换这里
gaode_base_url: https://restapi.amap.com
gaode_timeout: 5
```

> 可在 [高德开放平台](https://console.amap.com/) 申请 Web 服务类型的 API Key。

### 3. 模型配置

编辑 `config/rag.yml` 可调整所使用的模型：

```yaml
# config/rag.yml
chat_model_name: qwen3-max          # 对话大模型
embedding_model_name: text-embedding-v4  # 向量化模型
```

### 4. 向量库配置

编辑 `config/chroma.yml` 可调整 RAG 检索参数：

```yaml
# config/chroma.yml
collection_name: agent
persist_directory: chroma_db
k: 3                    # 检索返回的最相关文档数量
data_path: data
md5_hex_store: md5.text
allow_knowledge_file_type: ["txt", "pdf"]
chunk_size: 200         # 文本分块大小
chunk_overlap: 20       # 分块重叠长度
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install streamlit langchain langchain-core langchain-community langgraph \
            langchain-chroma chromadb dashscope pypdf pyyaml
```

### 3. 配置 API Key

```bash
# 设置阿里云 DashScope API Key
export DASHSCOPE_API_KEY="your_dashscope_api_key"

# 在 config/agent.yml 中配置高德地图 API Key
```

### 4. 启动应用

```bash
streamlit run app.py
```

浏览器将自动打开 `http://localhost:8501`，即可开始对话。

---

## 🔮 后续优化方向

- 向量数据库增加Muvils支持（更适合生产部署）
- MCP协议
- 增加用户身份认证与多用户会话隔离
- 改为异步处理

---

## 📄 许可证

本项目仅供学习与参考使用。
感谢黑马程序员开源免费项目、阿里云和高德地图等开放平台。
