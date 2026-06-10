[README.md](https://github.com/user-attachments/files/28784069/README.md)
# DeepAgents 深度搜索 —— 多智能体协作研究系统

> 基于 [DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) 框架构建的 **「深度搜索研究员」**，以「主智能体统筹 + 多专家子智能体并行协作」为核心架构，通过 **搜索 - 阅读 - 反思 - 再搜索** 的多轮迭代，突破传统 RAG 的单次检索局限，实现广覆盖、高精准、强可靠的复杂信息处理与文档生成。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/DeepAgents-0.1.0+-green.svg" alt="DeepAgents">
  <img src="https://img.shields.io/badge/LangGraph-0.1.0+-orange.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 📖 项目背景

在过去短短数年间，人工智能从最初仅能「响应问题」的 LLM，逐步迭代为具备「调用工具、落地执行」能力的 AI Agent，如今更朝着拥有协作意识、可驾驭复杂工作流的 **Agentic AI** 加速迈进。

本项目是 **DeepAgents 框架的一个典型最佳实践**，旨在构建一个模拟人类高级研究员思维的**多路组合智能体系统**：

- **深度代理（Deep Agents）**：模型不再是「一次性输出答案」的黑盒，而是具备「规划 - 执行 - 反馈 - 迭代」闭环能力的智能主体
- **高阶提示（Higher-Order Prompts, HOPs）**：向模型传递「思考框架与推理范式」，从根源上提升决策精准度与执行可靠性

---

## 🧠 核心特性

### 1. 智能规划与任务分解
内置 `write_todos` 工具，将复杂任务分解为离散执行步骤，实时跟踪进度，根据新信息动态调整计划——就像一位有经验的项目经理。

### 2. 高效上下文管理
内置文件系统工具集（`ls`、`read_file`、`write_file`、`edit_file`），将大型上下文卸载到外部存储，有效防止上下文窗口溢出。

### 3. 子代理生成与并行协作
采用 **1 主 + N 专** 的多路组合模式，主智能体统一调度，三类专家子智能体各司其职、并行工作，实现上下文隔离与专业化分工。

### 4. 长期记忆能力
利用 LangGraph Store 实现跨线程持久内存，支持多会话间的知识共享——就像带「永久档案柜」的智能助手。

### 5. 人机交互（HITL）
对敏感操作（如删库、删文件）配置人工审批流程，支持批准 / 拒绝 / 编辑参数三种决策方式，保障系统安全。

### 6. 流式实时反馈
基于 WebSocket 全双工通信，将 Agent 的思考过程、工具调用、子代理委派等每一步实时推送到前端。

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                         用户指令 (WebSocket)                       │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (Uvicorn)                       │
│              RESTful API + WebSocket + 文件上传/下载                │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Main Agent (主智能体)                          │
│  职责：理解需求 → 拆解任务 → 调度子代理 → 汇总结果 → 生成交付物      │
│  工具：generate_markdown / convert_md_to_pdf / read_file_content   │
└──────┬──────────────────────┬──────────────────────┬──────────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 网络搜索助手   │    │ 数据库查询助手 │    │ RAGFlow 助手  │
│ Tavily API   │    │ MySQL        │    │ 知识库检索    │
│ 公开知识检索   │    │ 结构化数据查询 │    │ 私有文档检索   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    交付物生成 (Markdown → PDF)                     │
└──────────────────────────────────────────────────────────────────┘
```

### 三类专家子代理

| 子代理 | 职责 | 核心工具 | 执行策略 |
|:---|:---|:---|:---|
| **网络搜索助手** | 公开知识广域检索，支持多轮递进搜索 | `internet_search` (Tavily) | 至少 3 个角度，最多 5 次检索 |
| **数据库查询助手** | 企业结构化数据查询（药品/商品） | `list_sql_tables` / `get_table_data` / `execute_sql_query` | 查表结构 → 预览数据 → 执行 SQL |
| **RAGFlow 助手** | 企业私有知识库深度检索 | `get_assistant_list` / `create_ask_delete` | 发现知识库 → 多角度提问（≥3 次）→ 原始切片输出 |

---

## 🛠️ 技术栈

| 类别 | 技术 | 说明 |
|:---|:---|:---|
| **AI 框架** | LangChain / LangGraph / DeepAgents | 项目神经中枢，构建有状态的循环工作流 |
| **大模型** | Qwen-Max / GPT-4o / DeepSeek | 通过 OpenAI 兼容接口调用 |
| **Web 框架** | FastAPI + Uvicorn | 高性能异步 Web 服务 |
| **实时通信** | WebSocket | 全双工通信，实时推送 Agent 思考过程 |
| **搜索引擎** | Tavily Search API | 专为 AI 设计的结构化搜索 |
| **知识库** | RAGFlow | 企业级 RAG 引擎，连接本地知识库 |
| **数据库** | MySQL + mysql-connector-python | 结构化数据存储与查询 |
| **文档处理** | python-docx / pypdf / pandas / PyMuPDF | 多格式文件读写 |
| **数据校验** | Pydantic | Agent 状态结构与工具参数校验 |
| **并发隔离** | ContextVars + asyncio | 协程级会话隔离，防止数据串线 |
| **前端** | Node.js + Vite | 现代化 Web 交互界面 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 20.19.0+
- MySQL 8.0+（如需使用数据库查询功能）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/deep-search.git
cd deep-search
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API Key：

```ini
# LLM 配置
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your-api-key
LLM_QWEN_MAX=qwen-max

# Tavily 搜索
TAVILY_API_KEY=your-tavily-key

# RAGFlow 知识库（可选）
RAGFLOW_API_URL=http://your-ragflow-server
RAGFLOW_API_KEY=your-ragflow-key

# MySQL 数据库（可选）
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=pharma_db
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

### 4. 初始化数据库（可选）

```bash
mysql -u root -p < sql/company_data.sql
```

### 5. 启动前端

```bash
cd ui
npm install
npm run dev
```

访问 `http://localhost:5173`

### 6. 启动后端

```bash
python api/server.py
```

服务运行在 `http://localhost:8000`

---

## 📂 项目结构

```
deep-search/
├── agent/                          # 智能体核心
│   ├── main_agent.py               # 主智能体组装与执行逻辑
│   ├── llm.py                      # 大模型初始化
│   ├── prompts.py                  # Prompt 配置加载
│   └── sub_agents/                 # 子智能体定义
│       ├── network_search_agent.py # 网络搜索助手
│       ├── database_query_agent.py # 数据库查询助手
│       └── knowledge_base_agent.py # RAGFlow 知识库助手
├── api/                            # Web 服务层
│   ├── server.py                   # FastAPI 入口
│   ├── context.py                  # ContextVars 会话隔离
│   ├── monitor.py                  # WebSocket 监控单例
│   └── logger.py                   # 分布式日志系统
├── tools/                          # 工具集
│   ├── tavily_tools.py             # 互联网搜索工具
│   ├── mysql_tools.py              # 数据库查询工具
│   ├── ragflow_tools.py            # RAGFlow 知识库工具
│   ├── markdown_tools.py           # Markdown 文档生成
│   ├── pdf_tools.py                # Markdown → PDF 转换
│   └── upload_file_read_tool.py    # 上传文件读取
├── prompt/                         # Prompt 配置
│   └── prompts.yml                 # 所有 Prompt 集中管理
├── utils/                          # 工具类
│   ├── path_utils.py               # 路径解析与清洗
│   └── word_converter.py           # Word COM 转 PDF
├── sql/                            # 数据库脚本
│   └── company_data.sql            # 模拟数据（制药公司）
├── ui/                             # 前端项目 (Vite + Node.js)
├── output/                         # 会话产物输出目录
├── updated/                        # 用户上传文件暂存区
├── .env                            # 环境变量配置
└── requirements.txt                # Python 依赖
```

---

## 🔌 API 接口

| 接口 | 方法 | 说明 |
|:---|:---|:---|
| `/api/task` | POST | 启动智能体任务 |
| `/api/upload` | POST | 上传文件（支持多文件） |
| `/api/download` | GET | 下载生成的文件 |
| `/api/files` | GET | 查询会话文件列表 |
| `/ws/{thread_id}` | WebSocket | 实时通讯（推送 Agent 思考过程） |

---

## 💡 使用场景

- **行业研究报告**：自动搜索公开信息 + 查询内部数据，生成多维度分析报告
- **企业数据问答**：自然语言查询数据库，无需编写 SQL
- **知识库深度检索**：对私有文档进行多角度、分层式提问
- **文件分析与报告生成**：上传文件后自动分析并生成 Markdown/PDF 报告
- **复杂信息聚合**：同时从网络、数据库、知识库三路获取信息并交叉验证

---

## 🧪 核心设计理念

### 多智能体三条铁律

只有在满足以下至少一条时，才值得承担多 Agent 的成本与复杂度：

1. **问题极度开放**：无标准答案或固定流程，需要灵活探索
2. **存在领域冲突**：跨两个及以上专业领域，需要物理隔离推理上下文
3. **需要多方向并行**：任务天然可拆分为互不依赖的子任务

### DeepAgents 框架家族

| 框架 | 角色 | 定位 |
|:---|:---|:---|
| **LangChain** | 做「动作」 | 核心代理框架，封装 LLM 与工具的交互 |
| **LangGraph** | 管「流程」 | 运行时，将执行变成可管理的图结构 |
| **DeepAgents** | 负责「组织」 | 内置规划器、子代理、文件系统、持久存储 |

---

## 📝 License

MIT © 2026

---

## 🙏 致谢

- [DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) - 深度代理框架
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架
- [LangGraph](https://langchain-ai.github.io/langgraph/) - 有状态 Agent 工作流
- [Tavily](https://tavily.com/) - AI 搜索引擎
- [RAGFlow](https://ragflow.io/) - 企业级 RAG 引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
