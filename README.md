# Merico Uncommented Functions Agent

一个智能的 Python 代理程序，用于批量获取 Merico 项目的未注释函数列表并进行深度数据归类分析。

## 功能特点

- **批量处理**: 自动读取项目 ID 列表并批量请求未注释函数数据
- **智能重试**: 请求失败时自动重试，确保数据完整性
- **数据归类**: 自动按严重程度、类型、规则等维度归类未注释函数数据
- **详细日志**: 记录所有操作过程，便于追踪和调试
- **灵活配置**: 支持配置文件，轻松调整参数
- **结果导出**: 生成原始数据、归类数据和可读报告

## 项目结构

```
mericoComment/
├── merico_agent.py              # 基础版智能体
├── merico_agent_advanced.py     # 高级版智能体（推荐）
├── config.json                  # 配置文件
├── repoIds_simple.json          # 项目 ID 列表
├── requirements.txt             # Python 依赖
├── README.md                    # 本文档
└── outputs/                     # 输出文件（运行后生成）
    ├── raw_results_*.json       # 原始响应数据
    ├── classified_results_*.json # ���类后数据
    ├── report_*.txt             # 分析报告
    └── merico_agent_*.log       # 运行日志
```

## 安装

### 1. 环境要求

- Python 3.7+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install requests
```

## 配置

### config.json 说明

```json
{
  "api_url": "API 请求地址",
  "token": "认证 Token",
  "repo_ids_file": "项目 ID 列表文件路径",
  "authors": ["作者过滤列表，留空表示不过滤"],
  "request_settings": {
    "batch_delay": 0.5,      // 请求间隔（秒）
    "retry_times": 3,         // 重试次数
    "retry_delay": 2,         // 重试延迟（秒）
    "timeout": 30,            // 请求超时（秒）
    "page_size": 100          // 每页数量
  },
  "output_settings": {
    "save_raw": true,         // 是否保存原始数据
    "save_classified": true,  // 是否保存归类数据
    "pretty_print": true      // 是否格式化 JSON
  }
}
```

### 修改配置

1. **更新 Token**: 如果 Token 过期，在 `config.json` 中更新 `token` 字段
2. **调整请求速度**: 修改 `batch_delay` 来控制请求间隔
3. **修改作者过滤**: 在 `authors` 数组中添加或删除作者邮箱

## 使用方法

### 方法一: 使用高级版（推荐）

高级版支持配置文件，功能更完善：

```bash
python merico_agent_advanced.py
```

使用自定义配置文件：

```bash
python merico_agent_advanced.py --config my_config.json
```

### 方法二: 使用基础版

基础版代码简单，适合学习和定制：

```bash
python merico_agent.py
```

## 输出说明

运行后会生成以下文件：

### 1. 原始数据 (raw_results_*.json)

包含所有项目的原始 API 响应数据：

```json
[
  {
    "repo_id": "项目ID",
    "data": {
      // API 原始响应
    },
    "timestamp": "请求时间"
  }
]
```

### 2. 归类数据 (classified_results_*.json)

按不同维度归类后的数据：

```json
{
  "summary": {
    "total_projects": 98,
    "successful_projects": 95,
    "failed_projects": 3,
    "total_uncommented_functions": 1234
  },
  "by_severity": {
    "high": 234,
    "medium": 567,
    "low": 433
  },
  "by_type": {
    "type1": 123,
    "type2": 456
  },
  "by_rule": {
    "rule1": 89,
    "rule2": 145
  },
  "all_uncommented_functions": [
    // 所有未注释函数的详细列表
  ],
  "errors": [
    // 失败的项目列表
  ]
}
```

### 3. ���析报告 (report_*.txt)

易读的文本格式报告：

```
================================================================================
Merico 项目未注释函数分析报告
================================================================================
生成时间: 2024-12-03 10:30:00

## 总体统计
- 总项目数: 98
- 成功项目数: 95
- 失败项目数: 3
- 总未注释函数数: 1234

## 按严重程度分类
- high: 234
- medium: 567
- low: 433

...
```

### 4. 运行日志 (merico_agent_*.log)

详细的运行日志，包含所有操作记录。

## 数据归类维度

智能体会自动从 API 响应中提取未注释函数数据并进行以下归类：

1. **按严重程度 (by_severity)**: 统计不同严重程度的未注释函数数量
2. **按类型 (by_type)**: 统计不同类型的未注释函数数量
3. **按规则 (by_rule)**: 统计触发不同规则的未注释函数数量
4. **按项目 (by_project)**: 每个项目的完整数据

## 高级功能

### 自定义归类逻辑

可以修改 `classify_data` 方法来添加自定义的归类维度：

```python
def classify_data(self, results):
    # 添加自定义归类逻辑
    classified["by_custom_field"] = defaultdict(int)

    for uncommented_func in uncommented_functions:
        custom_value = uncommented_func.get("custom_field")
        classified["by_custom_field"][custom_value] += 1

    return classified
```

### 添加数据过滤

在 `build_request_payload` 方法中修改过滤条件：

```python
"filter": {
    "authors": authors or [],
    "rules": ["specific_rule"],  # 只获取特定规则
    "severity": ["high"],         # 只获取高严重级别
    # ...
}
```

### 分页处理大数据

如果单个项目未注释函数数据量很大，可以实现分页：

```python
def fetch_all_pages(self, repo_id, authors=None):
    all_data = []
    page = 1
    while True:
        result = self.fetch_uncommented_functions(repo_id, authors, page)
        if not result or not result.get("data"):
            break
        all_data.append(result)
        page += 1
    return all_data
```

## 故障排查

### Token 过期

错误: `401 Unauthorized`

解决: 更新 `config.json` 中的 `token` 字段

### 请求频率过快

错误: `429 Too Many Requests`

解决: 增加 `config.json` 中的 `batch_delay` 值

### 网络超时

错误: `Connection timeout`

解决: 增加 `config.json` 中的 `timeout` 值

### 数据结构不匹配

如果 API 返回的数据结构与预期不符，需要修改 `classify_data` 方法中的数据提取逻辑。

## 开发建议

1. **先用基础版测试**: 使用基础版处理少量项目，验证 API 响应格式
2. **调整归类逻辑**: 根据实际 API 响应调整 `classify_data` ���法
3. **增量处理**: 对于大量项目，可以分批处理
4. **定期备份**: 重要数据记得备份

## 示例工作流

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 检查配置
cat config.json

# 3. 测试运行（可先编辑 repoIds_simple.json 只保留几个项目进行测试）
python merico_agent_advanced.py

# 4. 查看结果
ls -lh raw_results_*.json
ls -lh classified_results_*.json
cat report_*.txt

# 5. 分析日志
tail -f merico_agent_*.log
```

## 性能优化

### 并发请求

对于大量项目，可以使用并发请求提高效率：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_concurrent(self, max_workers=5):
    repo_ids = self.load_repo_ids()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.fetch_quality_functions, repo_id): repo_id
            for repo_id in repo_ids
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                self.all_results.append(result)
```

### 缓存机制

避免重复请求相同数据：

```python
import pickle
from pathlib import Path

def load_cache(self, cache_file="cache.pkl"):
    if Path(cache_file).exists():
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return {}

def save_cache(self, cache, cache_file="cache.pkl"):
    with open(cache_file, 'wb') as f:
        pickle.dump(cache, f)
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系开发团队。
