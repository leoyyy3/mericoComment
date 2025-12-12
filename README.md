# Merico 代码质量分析系统

一款专业的代码质量分析平台，专注于**未注释函数检测**、**重复代码识别**和**AI智能周报生成**，助力团队提升代码可维护性与开发效率。

## ✨ 核心功能

- **未注释函数分析**
  - 自动识别缺乏文档的函数
  - 按严重程度分级（高危/高/中/低）
  - 项目质量排名与可视化图表

- **重复代码检测**
  - 扫描跨仓库重复代码模式
  - 语言分布与复杂度影响分析
  - 交互式HTML报告展示

- **AI智能周报**
  - 基于TAPD提交记录生成报告
  - 支持自定义提示词定制内容
  - 自动导出HTML/Markdown格式

- **Web可视化界面**
  - 实时交互式仪表盘
  - 一键生成分析报告
  - 响应式移动端适配

- **API优先架构**
  - 完整RESTful接口支持
  - 定时任务自动执行
  - 全面错误处理机制

## 🗂 项目结构

```
mericoComment/
├── config/
│   ├── __init__.py
│   ├── loader.py       # 配置加载器
│   └── settings.py     # 类型安全配置
├── src/
│   ├── api/            # Flask API接口
│   │   ├── routes/     # 路由处理模块
│   │   └── app.py      # 应用工厂
│   ├── core/
│   │   ├── agents/     # 分析智能体
│   │   ├── analyzers/  # 数据处理器
│   │   ├── fetchers/   # 数据采集器
│   │   └── generators/ # 报告生成器
│   ├── services/       # 业务逻辑层
│   ├── utils/
│   │   ├── logger.py
│   │   ├── response.py
│   │   └── http_client.py
│   └── __init__.py
├── templates/
│   ├── web/            # HTML模板
│   └── report.html     # 报告模板
├── output/             # 生成报告目录
├── log/                # 系统日志目录
├── assets/
│   └── repoId_repoName_list.json
├── run.py              # CLI入口文件
├── repoIds_simple.json # 仓库ID列表
└── requirements.txt    # 依赖库清单
```

## ⚙️ 配置说明

### 创建 `config.json`

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false
  },
  "api_url": "https://merico.idc.hexun.com/buffet/api/tech_debt/function_doc_coverage",
  "duplicate_url": "https://merico.idc.hexun.com/buffet/api/tech_debt/duplicated_group",
  "token": "your-merico-token",
  "repo_ids_file": "repoIds_simple.json",
  "zhipu_ai": {
    "api_key": "your-zhipu-api-key",
    "model": "glm-4.5-flash"
  },
  "tapd": {
    "cookies": {
      "tapdsession": "your-session",
      "t_u": "your-t-u"
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

> 💡 **提示**：敏感数据建议通过环境变量配置（如 `MERICO_TOKEN`, `ZHIPU_API_KEY`）。

## 🚀 使用指南

### 1. 启动Web服务

```bash
python run.py serve --port 8080
```

访问仪表盘：`http://localhost:8080`

### 2. 执行分析任务

```bash
# 运行全部分析
python run.py analyze --type all

# 执行特定分析
python run.py analyze --type uncommented
python run.py analyze --type duplicate

# 生成周报
python run.py weekly \
  --entity-id "your-entity-id" \
  --workspace-id "your-workspace-id"
```

### 3. API接口列表

| 接口地址 | 方法 | 说明 |
|----------|--------|-------------|
| `/api/health` | GET | 服务健康检查 |
| `/api/status` | GET | 服务状态详情 |
| `/api/analysis/uncommented/run` | POST | 执行未注释分析 |
| `/api/analysis/duplicate/run` | POST | 执行重复代码分析 |
| `/api/weekly-report/generate` | POST | 生成AI周报 |
| `/api/analysis/reports` | GET | 报告列表查询 |

### 4. Web界面导航

- **仪表盘**：`http://localhost:8080`
- **重复代码报告**：`/duplicate-functions`
- **未注释函数报告**：`/uncommented-functions`

![仪表盘截图](screenshots/dashboard.png)

## 📊 报告功能亮点

### 交互式可视化
- 严重程度分布（环形图）
- 函数类型排名（柱状图）
- 项目质量排行榜

### 多格式导出
- 嵌入图表的HTML报告
- 数据分析专用CSV
- Markdown周报文档

### 报告示例

![报告样例](screenshots/report.png)

## ⚡ 高级用法

### 自定义报告提示词

```bash
python run.py weekly \
  --entity-id xxx \
  --prompt "重点关注本周性能优化内容"
```

### 数据深度分析

```bash
python run.py data-analyze \
  --file output/classified_results_20240101.json \
  --export-html
```

### 定时任务配置

在 `config.json` 中设置自动执行：

```json
"schedule": {
  "enabled": true,
  "hour": 7,
  "minute": 0
}
```

## 🔧 问题排查

| 问题现象 | 解决方案 |
|-------|----------|
| `401 Unauthorized` | 更新配置中的token |
| `429 Too Many Requests` | 增大batch_delay值 |
| 报告生成失败 | 检查output_dir目录权限 |
| TAPD连接异常 | 验证tapd配置中的cookies |

## 🌐 技术栈

- **后端框架**：Python 3.10+
- **Web框架**：Flask
- **AI引擎**：智谱AI（GLM-4.5）
- **任务调度**：APScheduler
- **数据可视化**：Chart.js
- **模板引擎**：Jinja2

## 📄 许可证

MIT 开源许可证