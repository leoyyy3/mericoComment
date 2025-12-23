# Merico 代码质量分析平台

> 集 **代码质量检测**、**可视化分析**、**AI 智能交互** 与 **异步任务处理** 于一体的企业级代码分析平台

基于 **Intelligent Agent** 架构，支持自然语言对话完成代码分析、周报生成和数据查询任务。

## 功能特性

### 代码质量分析

| 功能 | 描述 |
|------|------|
| **未注释函数检测** | 识别缺乏文档的关键函数，按严重程度分级（Critical/Warning/Info） |
| **重复代码扫描** | 跨仓库检测重复逻辑 (Copy-Paste)，提供优化建议 |
| **多维度图表** | 复杂度分布、类型排名、项目红黑榜等可视化报告 |
| **批量项目分析** | 支持配置多个项目 ID 进行批量分析 |

### AI 智能周报

- 基于 TAPD 提交记录自动生成结构化周报
- ZhipuAI (GLM-4.5-Flash) 深度分析，提取技术亮点
- 支持 Markdown 格式导出
- 自定义提示词模板

### 智能体助手

- **自然语言交互**：通过对话完成分析任务
- **意图识别**：自动识别分析请求、周报生成、状态查询
- **工具调用**：Function Calling 机制自动调度底层服务
- **会话管理**：支持多轮对话上下文保持

### 异步任务队列

- 基于 RQ (Redis Queue) 的异步任务处理
- 长时间分析任务后台执行
- 实时任务状态查询
- 支持任务监控面板 (RQ Dashboard)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Web 界面 (Flask + Jinja2)                    │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │  Token 配置   │  │  分析报告    │  │   AI 对话    │          │
│   └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                        Flask 后端                                │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│   │ Analysis   │ │  Weekly    │ │   Chat     │ │   Task     │   │
│   │   Route    │ │   Route    │ │   Route    │ │   Route    │   │
│   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘   │
└─────────┼──────────────┼──────────────┼──────────────┼──────────┘
          │              │              │              │
┌─────────▼──────────────▼──────────────▼──────────────▼──────────┐
│                       Services 层                                │
│     AnalysisService     WeeklyService     AgentService          │
└─────────┬──────────────┬──────────────┬─────────────────────────┘
          │              │              │
┌─────────▼──────────────▼──────────────▼─────────────────────────┐
│                        Core 模块                                 │
│   Agents / Fetchers / Analyzers / Generators                    │
└─────────┬──────────────┬──────────────┬─────────────────────────┘
          │              │              │
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Merico   │   │  TAPD    │   │ ZhipuAI  │   │  Redis   │
    │   API    │   │   API    │   │   API    │   │  Queue   │
    └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## 项目结构

```
mericoComment/
├── src/                           # 源代码主目录
│   ├── api/                       # Flask REST API
│   │   ├── app.py                 # 应用工厂 (含定时任务配置)
│   │   └── routes/                # 路由蓝图
│   │       ├── analysis.py        # 分析 API
│   │       ├── weekly.py          # 周报 API
│   │       ├── chat.py            # 对话 API
│   │       ├── task_route.py      # 异步任务 API
│   │       ├── web.py             # 页面路由
│   │       └── health.py          # 健康检查
│   ├── services/                  # 业务服务层
│   │   ├── analysis_service.py    # 分析业务逻辑
│   │   └── weekly_service.py      # 周报业务逻辑
│   ├── agent/                     # AI 智能体模块
│   │   ├── service.py             # Agent 对话服务 (LLM 调用、状态管理)
│   │   ├── tools.py               # 工具注册表 (Function Calling)
│   │   └── prompts.py             # 系统提示词管理
│   ├── core/                      # 核心业务逻辑
│   │   ├── agents/                # 数据采集智能体
│   │   │   └── uncommented_agent.py
│   │   ├── fetchers/              # 数据获取器
│   │   │   └── duplicate_fetcher.py
│   │   ├── analyzers/             # 数据分析器
│   │   │   ├── data_analyzer.py
│   │   │   └── duplicate_display.py
│   │   └── generators/            # 报告生成器
│   │       └── weekly_generator.py
│   ├── tasks/                     # 异步任务队列 (RQ)
│   │   ├── connection.py          # Redis 连接管理
│   │   ├── queues.py              # 队列配置
│   │   └── analysis_jobs.py       # 分析任务定义
│   └── utils/                     # 工具类库
│       ├── logger.py              # 统一日志工厂
│       ├── http_client.py         # HTTP 客户端 (重试机制)
│       ├── response.py            # API 响应格式化
│       └── retry.py               # 重试装饰器
├── config/                        # 配置管理模块
│   ├── settings.py                # 配置类定义 (dataclass)
│   └── loader.py                  # 配置加载器
├── templates/                     # Jinja2 HTML 模板
│   ├── base.html                  # 基础模板 (含 Chat Widget)
│   ├── report.html                # 分析报告模板
│   └── web/                       # 页面模板
├── static/                        # 静态资源
│   ├── css/style.css              # 全局样式 (Glassmorphism)
│   └── js/                        # 前端脚本
│       ├── chat.js                # Chat Widget 逻辑
│       ├── analysis-page.js       # 分析页面逻辑
│       └── task-manager.js        # 任务管理逻辑
├── output/                        # 输出目录 (自动创建)
│   ├── weekly_reports/            # 周报保存位置
│   └── *.json                     # 分析结果
├── log/                           # 日志目录 (自动创建)
├── run.py                         # CLI 启动入口
├── worker.py                      # RQ Worker 启动脚本
├── config.json                    # 主配置文件
├── config.json.template           # 配置模板
├── repoIds_simple.json            # 项目 ID 列表
└── requirements.txt               # Python 依赖
```

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- Redis (用于异步任务队列，可选)

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd mericoComment

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置文件

复制配置模板并修改：

```bash
cp config.json.template config.json
```

编辑 `config.json`：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false
  },
  "api_url": "https://your-merico-api/buffet/re/quality/listFunctions",
  "duplicate_url": "https://your-merico-api/buffet/api/tech_debt/duplicated_group",
  "token": "your-merico-token",
  "repo_ids_file": "repoIds_simple.json",
  "zhipu_ai": {
    "api_key": "your-zhipu-api-key",
    "model": "glm-4.5-flash"
  },
  "tapd": {
    "base_url": "https://www.tapd.cn/api/devops/source_code",
    "cookies": {
      "tapdsession": "your-session",
      "t_u": "your-t-u",
      "dsc-token": "your-dsc-token"
    }
  },
  "request_settings": {
    "timeout": 30,
    "retry_times": 3,
    "retry_delay": 2.0,
    "batch_delay": 0.5,
    "page_size": 100
  },
  "output_settings": {
    "output_dir": "output",
    "log_dir": "log",
    "save_classified": true,
    "pretty_print": true
  },
  "schedule": {
    "enabled": true,
    "hour": 7,
    "minute": 0
  }
}
```

### 4. 启动服务

```bash
# 启动 Web 服务
python run.py serve --port 8080

# 可选：启动异步任务 Worker
python worker.py
```

访问 **http://localhost:8080**

---

## CLI 命令

### 启动 Web 服务

```bash
python run.py serve [OPTIONS]

选项:
  --host              绑定地址 (默认: 0.0.0.0)
  --port, -p          端口号 (默认: 8080)
  --debug, -d         调试模式（仅开发模式）
  --production, --prod 生产模式（使用 Gunicorn）
  --workers, -w       Worker 进程数（仅生产模式）
  --config, -c        配置文件路径

示例:
  # 开发模式（Flask 内置服务器）
  python run.py serve --port 8080 --debug

  # 生产模式（Gunicorn）
  python run.py serve --production
  python run.py serve --production --workers 4 --port 8080

  # 或直接使用 Gunicorn
  gunicorn -c gunicorn.conf.py wsgi:app
```

### 运行代码分析

```bash
python run.py analyze --type [all|uncommented|duplicate]

示例:
  python run.py analyze --type all          # 运行所有分析
  python run.py analyze --type uncommented  # 仅分析未注释函数
  python run.py analyze --type duplicate    # 仅分析重复代码
```

### 分析已有数据

```bash
python run.py data-analyze --file <path> [--export-csv] [--export-html]

示例:
  python run.py data-analyze -f output/classified_results_xxx.json --export-html
```

### 生成周报

```bash
python run.py weekly --entity-id <id> --workspace-id <id> [OPTIONS]

选项:
  --prompt, -P      自定义提示词
  --no-save         不保存到文件
  --print-report    打印周报内容

示例:
  python run.py weekly -e 123456 -w 789012 --print-report
```

### 获取重复函数数据

```bash
python run.py fetch-duplicate
```

---

## API 文档

### 分析接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/analysis/uncommented/run` | POST | 运行未注释函数分析 |
| `/api/analysis/duplicate/run` | POST | 运行重复代码分析 |
| `/api/analysis/all/run` | POST | 运行所有分析 |
| `/api/analysis/reports` | GET | 获取报告列表 |
| `/api/analysis/reports/<filename>` | GET | 下载报告文件 |

**请求体** (可选)：

```json
{
  "token": "Bearer Token (可选，覆盖配置文件中的 token)"
}
```

### 异步任务接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/tasks/analyze/uncommented` | POST | 提交未注释分析任务 |
| `/api/tasks/analyze/duplicate` | POST | 提交重复分析任务 |
| `/api/tasks/analyze/all` | POST | 提交完整分析任务 |
| `/api/tasks/<task_id>/status` | GET | 查询任务状态 |

**响应示例**：

```json
{
  "success": true,
  "data": {
    "task_id": "abc123",
    "status": "queued"
  }
}
```

### 周报接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/weekly-report/generate` | POST | 生成周报 |

**请求体**：

```json
{
  "entity_id": "123456",
  "workspace_id": "789012",
  "prompt": "可选的自定义提示词"
}
```

### 对话接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/chat/session` | POST | 创建对话会话 |
| `/api/chat/message` | POST | 发送对话消息 |
| `/api/chat/history/<session_id>` | GET | 获取对话历史 |

**发送消息示例**：

```json
{
  "session_id": "uuid",
  "message": "分析所有项目的未注释函数",
  "token": "可选的 Merico Token"
}
```

### 系统接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/status` | GET | 服务状态详情 |

### Web 页面

| 路径 | 描述 |
|------|------|
| `/` | 首页 |
| `/duplicate-functions` | 重复代码分析页 |
| `/uncommented-functions` | 未注释函数分析页 |

---

## 前端 Token 配置

由于 Merico API Token 每日更新，系统支持在 Web 界面直接配置：

1. 打开首页
2. 在 **Token 配置** 区域输入新的 Token
3. 点击 **保存** 按钮
4. Token 保存在浏览器 localStorage，刷新不丢失
5. 运行分析时自动使用保存的 Token

**Token 优先级**：前端 Token > config.json Token > 环境变量

---

## 环境变量

支持通过环境变量覆盖配置：

| 变量名 | 描述 |
|--------|------|
| `ENV` | 运行环境 (development/production) |
| `SERVER_HOST` | 服务绑定地址 |
| `SERVER_PORT` | 服务端口 |
| `DEBUG` | 调试模式 (true/false) |
| `MERICO_TOKEN` | Merico API Token |
| `MERICO_API_URL` | Merico API 地址 |
| `ZHIPU_API_KEY` | 智谱 AI API Key |
| `ZHIPU_MODEL` | 智谱 AI 模型名称 |
| `TAPD_BASE_URL` | TAPD API 地址 |
| `REDIS_URL` | Redis 连接地址 |

**优先级**：环境变量 > config.json > 默认值

---

## 异步任务

### 启动 Worker

```bash
# 启动单个 Worker
python worker.py

# 或使用 rq 命令
rq worker --url redis://localhost:6379
```

### 监控面板

安装 `rq-dashboard` 后可启动监控：

```bash
rq-dashboard --redis-url redis://localhost:6379
```

访问 **http://localhost:9181** 查看任务队列状态。

---

## 输出文件

```
output/
├── classified_results_YYYYMMDD_HHMMSS.json     # 分类的分析结果
├── uncommented_functions_report_*.html         # 未注释函数 HTML 报告
├── duplicate_functions_report_*.html           # 重复代码 HTML 报告
└── weekly_reports/
    └── weekly_report_*_YYYYMMDD_HHMMSS.md      # Markdown 周报

log/
└── api_YYYYMMDD_HHMMSS.log                     # 应用日志
```

---

## 定时任务

系统内置 APScheduler 定时任务，可在 `config.json` 中配置：

```json
{
  "schedule": {
    "enabled": true,
    "hour": 7,
    "minute": 0
  }
}
```

启用后，每天指定时间自动运行代码分析任务。

---

## 问题排查

| 问题 | 解决方案 |
|------|----------|
| `401 Unauthorized` | 检查 Token 是否过期，在前端重新配置 |
| `429 Too Many Requests` | 增大 `request_settings.batch_delay` 值 |
| 报告生成失败 | 检查 `output` 目录权限 |
| 智能体无响应 | 检查 `zhipu_ai.api_key` 是否正确 |
| TAPD 连接异常 | 重新登录 TAPD 获取 cookies |
| Redis 连接失败 | 确保 Redis 服务运行，检查连接地址 |
| 异步任务不执行 | 确保 Worker 进程已启动 |

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **Backend** | Python 3.10+, Flask, APScheduler, Gunicorn |
| **AI/LLM** | ZhipuAI (GLM-4.5-Flash) |
| **Task Queue** | RQ (Redis Queue), Redis |
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JavaScript |
| **Visualization** | Chart.js |
| **Template** | Jinja2 |
| **HTTP Client** | Requests (with retry) |

---

## 开发指南

### 代码规范

- 遵循 PEP 8 规范
- 使用 `typing` 模块添加类型注解
- 使用 `src.utils.LoggerFactory` 而非 `print`
- 使用 `pathlib.Path` 处理文件路径
- 错误处理使用 `try/except` 并记录完整 traceback

### 添加新的分析工具

1. 在 `src/core/agents/` 创建新的数据采集类
2. 在 `src/core/analyzers/` 创建对应的分析器
3. 在 `src/services/` 添加服务层封装
4. 在 `src/agent/tools.py` 注册为 Agent 工具
5. 在 `src/api/routes/` 添加 API 路由

### 日志使用

```python
from src.utils import LoggerFactory

logger = LoggerFactory.get_logger(__name__)
logger.info("Processing started")
logger.error("Error occurred", exc_info=True)
```

---

## License

MIT License
