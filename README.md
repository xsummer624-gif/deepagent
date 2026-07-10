# DeepAgents 深度搜索 —— 多智能体协作研究系统

> 基于 [DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) 框架构建的「深度搜索研究员」，以「主智能体统筹 + 多专家子智能体并行协作」为核心架构，通过「搜索 - 阅读 - 反思 - 再搜索」的多轮迭代，突破传统 RAG 的单次检索局限，实现广覆盖、高精准、强可靠的复杂信息处理与文档生成。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/DeepAgents-0.1.0+-green.svg" alt="DeepAgents">
  <img src="https://img.shields.io/badge/LangGraph-0.1.0+-orange.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.5-brightgreen.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 项目背景

在人工智能从「响应问题」的 LLM 迭代为具备「调用工具、落地执行」能力的 AI Agent，再到可驾驭复杂工作流的 Agentic AI 的进程中，本项目是 **DeepAgents 框架的一个典型最佳实践**，构建一个模拟人类高级研究员思维的**多路组合智能体系统**。

---

## 核心特性

### 1. 子代理生成与并行协作
采用 **1 主 + N 专** 的多路组合模式，主智能体统一调度，三类专家子智能体各司其职、并行工作，实现上下文隔离与专业化分工。

### 2. 高效上下文管理
内置文件读写工具（`generate_markdown` / `read_file_content`），将上下文卸载到会话工作目录，配合 ContextVars 实现协程级会话隔离，防止并发请求串线。

### 3. 流式实时反馈
基于 WebSocket 全双工通信，将 Agent 的思考过程、工具调用、子代理委派等每一步实时推送到前端。

### 4. 会话级记忆
基于 LangGraph `InMemorySaver` 实现单进程内的会话上下文记忆（重启后丢失，适合开发与演示）。

### 5. 安全防护
- SQL 查询仅允许单条只读 SELECT，禁止堆叠查询与危险关键字
- 文件下载/列表接口仅允许访问输出目录，防止路径遍历
- 前端 Markdown 渲染经 DOMPurify 净化，防 XSS

---

## 系统架构

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
│  工具：generate_markdown / read_file_content                       │
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
│                    交付物生成 (Markdown)                           │
└──────────────────────────────────────────────────────────────────┘
```

### 三类专家子代理

| 子代理 | 职责 | 核心工具 | 执行策略 |
|:---|:---|:---|:---|
| **网络搜索助手** | 公开知识广域检索，支持多轮递进搜索 | `internet_search` (Tavily) | 至少 3 个角度，最多 5 次检索 |
| **数据库查询助手** | 企业结构化数据查询（药品） | `list_sql_tables` / `get_table_data` / `execute_sql_query` | 查表结构 → 预览数据 → 执行 SQL |
| **RAGFlow 助手** | 企业私有知识库深度检索 | `get_assistant_list` / `create_ask_delete` | 发现知识库 → 多角度提问（≥3 次）→ 原始切片输出 |

---

## 技术栈

| 类别 | 技术 | 说明 |
|:---|:---|:---|
| **AI 框架** | LangChain / LangGraph / DeepAgents | 项目神经中枢，构建有状态的循环工作流 |
| **大模型** | DeepSeek / Qwen-Max / GPT-4o | 通过 OpenAI 兼容接口调用，环境变量自动回退 |
| **Web 框架** | FastAPI + Uvicorn | 高性能异步 Web 服务 |
| **实时通信** | WebSocket | 全双工通信，实时推送 Agent 思考过程 |
| **搜索引擎** | Tavily Search API | 专为 AI 设计的结构化搜索 |
| **知识库** | RAGFlow | 企业级 RAG 引擎，连接本地知识库 |
| **数据库** | MySQL + mysql-connector-python | 结构化数据存储与查询 |
| **数据校验** | Pydantic | Agent 状态结构与工具参数校验 |
| **并发隔离** | ContextVars + asyncio | 协程级会话隔离，防止数据串线 |
| **前端** | Vue 3 + Vite + TypeScript | 现代化 Web 交互界面 |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20+
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

```bash
cp .env.example .env
```

```ini
# LLM 配置（DeepSeek 优先，缺失时回退到 OPENAI_* / LLM_QWEN_MAX）
DEEPSEEK_MODEL_R=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=your-api-key

# 备选：OpenAI 兼容接口
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
mysql -u root -p < db/schema.sql
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

> 前端默认连接 `http://localhost:8000`，可通过 `.env` 中的 `VITE_API_BASE` / `VITE_WS_BASE` 覆盖。

### 6. 启动后端

```bash
python api/server.py
```

服务运行在 `http://localhost:8000`

---

## 项目结构

```
deep-search/
├── agent/                          # 智能体核心
│   ├── main_agent.py               # 主智能体组装与执行逻辑（延迟初始化）
│   ├── llm.py                      # 大模型初始化（兼容多套环境变量）
│   ├── prompts.py                  # Prompt 配置加载（YAML）
│   └── subagents/                  # 子智能体定义
│       ├── network_search_agent.py # 网络搜索助手
│       ├── database_query_agent.py # 数据库查询助手
│       └── knowledge_base_agent.py # RAGFlow 知识库助手
├── api/                            # Web 服务层
│   ├── server.py                   # FastAPI 入口
│   ├── context.py                  # ContextVars 会话隔离
│   ├── monitor.py                  # WebSocket 监控单例
│   └── logger.py                   # 分布式日志系统
├── tools/                          # 工具集
│   ├── tavily_tool.py              # 互联网搜索工具
│   ├── db_tools.py                 # 数据库查询工具（含 SQL 安全校验）
│   ├── ragflow_tools.py            # RAGFlow 知识库工具
│   ├── markdown_tools.py           # Markdown 文档生成
│   └── upload_file_read_tool.py    # 上传文件读取
├── prompt/                         # Prompt 配置
│   └── prompts.yml                 # 所有 Prompt 集中管理
├── utils/                          # 工具类
│   └── path_utils.py               # 路径解析与清洗
├── db/                             # 数据库脚本
│   └── schema.sql                  # 模拟数据（制药公司）
├── ragflow/                        # RAGFlow SDK 示例与配置
├── frontend/                       # 前端项目 (Vue 3 + Vite + TS)
├── output/                         # 会话产物输出目录
├── updated/                        # 用户上传文件暂存区
├── .env.example                    # 环境变量模板
└── requirements.txt                # Python 依赖
```

---

## API 接口

| 接口 | 方法 | 说明 |
|:---|:---|:---|
| `/api/task` | POST | 启动智能体任务（同会话重复派发返回 409） |
| `/api/upload` | POST | 上传文件（支持多文件） |
| `/api/download` | GET | 下载生成的文件（相对路径，仅限 output 目录） |
| `/api/files` | GET | 查询会话文件列表（相对路径，仅限 output 目录） |
| `/outputs/{path}` | 静态 | 直接访问 output 目录下的生成文件 |
| `/ws/{thread_id}` | WebSocket | 实时通讯（推送 Agent 思考过程） |

---

## 使用场景

- **行业研究报告**：自动搜索公开信息 + 查询内部数据，生成多维度分析报告
- **企业数据问答**：自然语言查询数据库，无需编写 SQL
- **知识库深度检索**：对私有文档进行多角度、分层式提问
- **文件分析与报告生成**：上传文件后自动分析并生成 Markdown 报告
- **复杂信息聚合**：同时从网络、数据库、知识库三路获取信息并交叉验证

---

## 核心设计理念

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

## License

MIT © 2026

---

## 致谢

- [DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) - 深度代理框架
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架
- [LangGraph](https://langchain-ai.github.io/langgraph/) - 有状态 Agent 工作流
- [Tavily](https://tavily.com/) - AI 搜索引擎
- [RAGFlow](https://ragflow.io/) - 企业级 RAG 引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
