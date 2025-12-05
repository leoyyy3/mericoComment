# HTML 模板说明

## 概述

此目录包含用于生成未注释函数分析报告的 Jinja2 HTML 模板。

## 模板文件

### report.html

主报告模板,用于生成可视化的 HTML 分析报告。

#### 可用变量

- `generation_time`: 报告生成时间 (字符串)
- `summary`: 汇总数据字典
  - `total_projects`: 总项目数
  - `successful_projects`: 成功项目数
  - `failed_projects`: 失败项目数
  - `total_uncommented_functions`: 总未注释函数数
- `severity_labels`: 严重程度标签列表
- `severity_data`: 严重程度数据列表
- `severity_colors`: 严重程度颜色列表
- `type_labels`: 类型标签列表 (Top 15)
- `type_data`: 类型数据列表 (Top 15)
- `project_rankings`: 项目排名列表 [(排名, (项目ID, 未注释函数数))]

## 自定义模板

### 修改样式

在 `<style>` 标签中修改 CSS 样式:

```css
.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* 修改为你喜欢的颜色 */
}
```

### 添加新图表

1. 在适当位置添加 canvas 元素:
```html
<canvas id="myNewChart"></canvas>
```

2. 在 `<script>` 部分添加 Chart.js 配置:
```javascript
const myCtx = document.getElementById('myNewChart').getContext('2d');
new Chart(myCtx, {
    // 图表配置
});
```

### 修改表格结构

在 `<table>` 部分修改表头和数据行:

```html
<thead>
    <tr>
        <th>新列</th>
        <!-- 其他列 -->
    </tr>
</thead>
```

## 注意事项

- 使用 Jinja2 语法进行模板渲染
- 数字格式化使用 `"{:,}".format(number)` 添加千位分隔符
- 使用 `| tojson` 过滤器将 Python 数据转换为 JavaScript
- 保持响应式设计,确保在不同屏幕尺寸下正常显示
