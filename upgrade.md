analyze_data.py 主要优化方向

  1. 模板分离 ⭐⭐⭐（高优先级）

  问题：第344-669行有大量HTML硬编码在Python代码中，难以维护和修改。

  改进方案：
  - 使用 Jinja2 模板引擎或将HTML分离到独立文件
  - 或使用 Python 的字符串模板类

  2. 消除魔法数字 ⭐⭐⭐（高优先级）

  问题：代码中有大量硬编码数字（20, 40, 80等）。

  改进方案：
  class Config:
      """配置常量"""
      TOP_N_ITEMS = 20
      TOP_PROJECTS_BEST = 10
      BAR_CHART_WIDTH = 40
      SECTION_WIDTH = 80
      TOP_RANKING_THRESHOLD = 3
      MEDIUM_RANKING_THRESHOLD = 10

  3. 添加类型注解 ⭐⭐（中优先级）

  问题：缺少类型提示，降低代码可读性和IDE支持。

  改进方案：
  from typing import Dict, List, Any, Optional

  def load_data(self) -> Dict[str, Any]:
      """加载数据"""

  def analyze_severity_distribution(self) -> None:
      """分析严重程度分布"""

  4. 重构超长方法 ⭐⭐⭐（高优先级）

  问题：export_html 方法长达340行，职责过重。

  改进方案：拆分为多个小方法：
  def export_html(self, output_file: str = "..."):
      html_content = self._generate_html_structure()
      self._write_html_file(output_file, html_content)

  def _generate_html_structure(self) -> str:
      return f"""
      {self._get_html_header()}
      {self._get_html_body()}
      {self._get_html_footer()}
      """

  def _get_html_header(self) -> str:
      """生成HTML头部"""

  def _get_html_body(self) -> str:
      """生成HTML主体"""

  5. 改进数据缓存 ⭐⭐（中优先级）

  问题：多处重复计算项目统计数据（第170-174行，第338-342行）。

  改进方案：
  from functools import lru_cache

  @property
  @lru_cache(maxsize=1)
  def project_function_count(self) -> Counter:
      """缓存项目函数统计"""
      counter = Counter()
      for func in self.data.get("all_uncommented_functions", []):
          if repo_id := func.get("repo_id"):
              counter[repo_id] += 1
      return counter

  6. 输出与逻辑分离 ⭐⭐（中优先级）

  问题：分析方法直接打印，难以测试和复用。

  改进方案：
  def analyze_severity_distribution(self) -> Dict[str, Any]:
      """返回分析结果而不是打印"""
      by_severity = self.data.get("by_severity", {})
      total = sum(by_severity.values())

      return {
          'by_severity': by_severity,
          'total': total,
          'sorted_items': sorted(by_severity.items(), ...)
      }

  def print_severity_distribution(self):
      """专门负责打印"""
      result = self.analyze_severity_distribution()
      # 打印逻辑

  7. 改进颜色管理 ⭐（低优先级）

  问题：Colors类使用可变类属性，不够优雅。

  改进方案：
  from dataclasses import dataclass

  @dataclass
  class ColorScheme:
      """颜色方案"""
      header: str = '\033[95m'
      blue: str = '\033[94m'
      # ... 其他颜色

      @classmethod
      def no_color(cls) -> 'ColorScheme':
          """返回无颜色方案"""
          return cls(header='', blue='', ...)

  # 使用
  colors = ColorScheme() if not args.no_color else ColorScheme.no_color()

  8. 错误处理细化 ⭐⭐（中优先级）

  问题：第57行使用泛化的 except Exception。

  改进方案：
  def load_data(self) -> Dict[str, Any]:
      try:
          with open(self.classified_file, 'r', encoding='utf-8') as f:
              return json.load(f)
      except FileNotFoundError:
          print(f"错误: 文件不存在 {self.classified_file}")
          sys.exit(1)
      except json.JSONDecodeError as e:
          print(f"错误: JSON格式无效 - {e}")
          sys.exit(1)
      except PermissionError:
          print(f"错误: 没有读取权限")
          sys.exit(1)

  9. 使用现代Python特性 ⭐（低优先级）

  改进：
  - 使用海象运算符（已在某些地方使用）
  - 使用 pathlib 替代字符串路径操作
  - 使用 f-string 统一字符串格式化

  10. 配置文件支持 ⭐（低优先级）

  改进：添加配置文件支持，允许自定义颜色、阈值等：
  # config.yaml
  display:
    top_n: 20
    bar_width: 40
  colors:
    enabled: true
  export:
    csv_encoding: utf-8-sig

  建议的优化优先级

  第一阶段（快速改进）：
  1. 消除魔法数字，添加配置类
  <!-- 2. 添加类型注解 -->
  3. 细化错误处理

  第二阶段（结构优化）：
  4. 拆分 export_html 方法
  5. 添加数据缓存
  6. 分离输出与逻辑

  第三阶段（架构改进）：
  7. HTML模板分离
  8. 改进颜色管理