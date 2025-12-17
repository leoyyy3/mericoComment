# Merico 代码质量分析平台

一款集 **代码质量检测**、**可视化分析** 与 **AI 智能交互** 于一体的综合平台。

通过 **Intelligent Agent** 架构，支持自然语言对话完成代码分析、周报生成和数据查询任务。

## 核心功能

### 代码质量分析

| 功能 | 描述 |
|------|------|
| **未注释函数检测** | 识别缺乏文档的关键函数，按严重程度分级 |
| **重复代码扫描** | 跨仓库检测重复逻辑 (Copy-Paste)，提供优化建议 |
| **多维度图表** | 复杂度分布、类型排名、项目红黑榜等可视化 |

### AI 智能周报

- 基于 TAPD 提交记录自动生成结构化周报
- ZhipuAI (GLM-4) 深度分析，提取技术亮点
- 支持 Markdown 和 HTML 导出

### 智能体助手

- **自然语言交互**：通过对话完成分析任务
- **意图识别**：自动识别分析请求、周报生成、状态查询
- **工具调用**：自动调度底层分析服务

### 前端 Token 配置

- 支持在 Web 界面直接配置 API Token
- Token 本地存储，刷新页面不丢失
- 适用于 Token 每日更新的场景

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 界面 (Flask + Jinja2)            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Token 配置  │  │ 分析报告    │  │ AI 对话     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────┐
│                    Flask 后端                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Analysis BP │  │ Weekly BP   │  │ Chat BP     │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                    Services 层                          │
│  AnalysisService    WeeklyService    AgentService      │
└─────────┬────────────────┬────────────────┬─────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                    Core 模块                            │
│  Agents / Fetchers / Analyzers / Generators            │
└─────────┬────────────────┬────────────────┬─────────────┘
          │                │                │
          ▼                ▼                ▼
    Merico API         TAPD API        ZhipuAI API
```

---

## 项目结构

```
mericoComment/
├── src/
│   ├── api/                    # Flask API
│   │   ├── app.py              # 应用工厂
│   │   └── routes/             # 路由模块
│   │       ├── analysis.py     # 分析 API
│   │       ├── weekly.py       # 周报 API
│   │       ├── chat.py         # 对话 API
│   │       ├── web.py          # 页面路由
│   │       └── health.py       # 健康检查
│   ├── services/               # 业务服务层
│   │   ├── analysis_service.py
│   │   └── weekly_service.py
│   ├── core/                   # 核心业务逻辑
│   │   ├── agents/             # 数据采集智能体
│   │   ├── fetchers/           # 数据获取器
│   │   ├── analyzers/          # 数据分析器
│   │   └── generators/         # 报告生成器
│   ├── agent/                  # AI 智能体模块
│   │   ├── service.py          # 对话状态管理
│   │   ├── tools.py            # 工具注册表
│   │   └── prompts.py          # 提示词工程
│   └── utils/                  # 工具类
│       ├── http_client.py      # HTTP 客户端
│       ├── logger.py           # 日志工厂
│       └── response.py         # 响应格式化
├── config/                     # 配置管理
│   ├── loader.py               # 配置加载器
│   └── settings.py             # 配置定义
├── templates/                  # Jinja2 模板
│   ├── base.html               # 基础模板
│   └── web/                    # 页面模板
├── static/                     # 静态资源
│   ├── css/
│   └── js/
├── output/                     # 输出目录
├── config.json                 # 主配置文件
├── repoIds_simple.json         # 项目 ID 列表
├── run.py                      # 启动入口
└── requirements.txt            # 依赖清单
```

---

## 快速开始

### 1. 环境准备

```bash
# 确保 Python 3.10+ 已安装
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

创建 `config.json`：

```json
{
  "api_url": "https://merico.idc.hexun.com/buffet/re/quality/listFunctions",
  "duplicate_url": "https://merico.idc.hexun.com/buffet/api/tech_debt/duplicated_group",
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
      "t_u": "your-t-u"
    }
  },
  "request_settings": {
    "timeout": 30,
    "retry_times": 3,
    "retry_delay": 2,
    "batch_delay": 0.5,
    "page_size": 100
  },
  "output_settings": {
    "save_raw": true,
    "save_classified": true,
    "pretty_print": true
  }
}
```

### 3. 启动服务

```bash
python run.py serve --port 8080
```

访问 **http://localhost:8080**

---

## 前端 Token 配置

由于 Merico API Token 每日更新，系统支持在 Web 界面直接配置：

1. 打开首页
2. 在 **Token 配置** 区域输入新的 Token
3. 点击 **保存** 按钮
4. Token 保存在浏览器 localStorage，刷新不丢失
5. 运行分析时自动使用保存的 Token

**优先级**：前端 Token > config.json Token > 环境变量

---

## CLI 命令

### 启动 Web 服务

```bash
python run.py serve [OPTIONS]

# 选项:
#   --host       绑定地址 (默认: 0.0.0.0)
#   --port, -p   端口号 (默认: 8080)
#   --debug, -d  调试模式
#   --config, -c 配置文件路径
```

### 运行代码分析

```bash
python run.py analyze --type [all|uncommented|duplicate]

# 示例:
python run.py analyze --type all          # 运行所有分析
python run.py analyze --type uncommented  # 仅分析未注释函数
python run.py analyze --type duplicate    # 仅分析重复函数
```

### 分析已有数据

```bash
python run.py data-analyze --file <path> [--export-csv] [--export-html]

# 示例:
python run.py data-analyze -f output/classified_results_xxx.json --export-html
```

### 生成周报

```bash
python run.py weekly --entity-id <id> --workspace-id <id> [OPTIONS]

# 选项:
#   --prompt, -P      自定义提示词
#   --no-save         不保存到文件
#   --print-report    打印周报内容

# 示例:
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
| `/api/analysis/duplicate/run` | POST | 运行重复函数分析 |
| `/api/analysis/all/run` | POST | 运行所有分析 |
| `/api/analysis/reports` | GET | 获取报告列表 |
| `/api/analysis/reports/<filename>` | GET | 下载报告文件 |

**请求体** (可选)：

```json
{
  "token": "Bearer Token (可选，覆盖配置文件中的 token)"
}
```

### 周报接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/weekly-report/generate` | POST | 生成周报 |

### 对话接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/chat/session` | POST | 创建对话会话 |
| `/api/chat/message` | POST | 发送对话消息 |

### 系统接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/status` | GET | 服务状态 |

---

## 环境变量

支持通过环境变量覆盖配置：

| 变量名 | 描述 |
|--------|------|
| `MERICO_TOKEN` | Merico API Token |
| `MERICO_API_URL` | Merico API 地址 |
| `ZHIPU_API_KEY` | 智谱 AI API Key |

**优先级**：环境变量 > config.json > 默认值

---

## 问题排查

| 问题 | 解决方案 |
|------|----------|
| `401 Unauthorized` | 检查 Token 是否过期，在前端重新配置 |
| `429 Too Many Requests` | 增大 `batch_delay` 值 |
| 报告生成失败 | 检查 `output` 目录权限 |
| 智能体无响应 | 检查 `zhipu_ai.api_key` 是否正确 |
| TAPD 连接异常 | 重新登录获取 cookies |

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **Backend** | Python 3.10+, Flask, APScheduler |
| **AI** | ZhipuAI (GLM-4) |
| **Frontend** | HTML5, CSS3 (Glassmorphism), JavaScript |
| **Visualization** | Chart.js |
| **HTTP Client** | Requests |

---

## License

MIT License
