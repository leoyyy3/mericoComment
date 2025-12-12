架构优化建议

  1. 项目结构重组

  当前问题: 代码文件平铺在根目录，缺乏标准的 Python 包结构

  建议优化:
  mericoComment/
  ├── src/
  │   ├── __init__.py
  │   ├── core/                    # 核心业务逻辑
  │   │   ├── agents/              # 智能体模块
  │   │   ├── analyzers/           # 分析器模块
  │   │   └── fetchers/            # 数据获取模块
  │   ├── api/                     # API 统一入口
  │   │   ├── routes/
  │   │   └── middleware/
  │   ├── services/                # 业务服务层
  │   └── utils/                   # 公共工具
  ├── config/                      # 配置目录
  ├── tests/                       # 统一测试目录
  └── scripts/                     # 运行脚本

  ---
  2. 合并重复的 Web 服务

  当前问题: 存在两个独立的 Web 服务 (web_service.py 和
  weekly/api_service.py)，各自运行在不同端口

  建议: 合并为统一的 API Gateway，使用 Flask Blueprint 组织路由：

  # api/__init__.py
  from flask import Flask
  from .routes import weekly_bp, analysis_bp, health_bp

  def create_app():
      app = Flask(__name__)
      app.register_blueprint(weekly_bp, url_prefix='/api/weekly')
      app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
      app.register_blueprint(health_bp, url_prefix='/api')
      return app

  ---
  3. 抽象公共层

  当前问题: 多个模块存在重复代码，如 HTTP 请求、重试逻辑、日志配置

  建议抽取:

  | 公共组件              | 用途                      |
  |-------------------|-------------------------|
  | HttpClient        | 统一的 HTTP 请求封装，含重试、超时、认证 |
  | RetryDecorator    | 可复用的重试装饰器               |
  | LoggerFactory     | 统一日志配置                  |
  | ConfigLoader      | 集中配置管理                  |
  | ResponseFormatter | 统一 API 响应格式             |

  ---
  4. 配置管理优化

  当前问题:
  - 敏感信息(API Key、Token)存放在 config.json
  - 缺乏环境区分（dev/prod）

  建议:
  # 使用环境变量 + 配置文件分层
  config/
  ├── default.py       # 默认配置
  ├── development.py   # 开发环境
  ├── production.py    # 生产环境
  └── __init__.py      # 根据 ENV 自动加载

  # 敏感信息通过环境变量注入
  ZHIPU_API_KEY=xxx
  TAPD_SESSION=xxx

  ---
  5. 引入异步处理

  当前问题: merico_agent_advanced.py 批量请求数百个项目时是同步串行的，效率低

  建议: 使用 asyncio + aiohttp 实现并发请求：

  async def fetch_all_projects(repo_ids: List[str]) -> List[dict]:
      async with aiohttp.ClientSession() as session:
          tasks = [fetch_project(session, rid) for rid in repo_ids]
          return await asyncio.gather(*tasks, return_exceptions=True)

  预期效果: 数百个项目的请求时间可从分钟级降到秒级

  ---
  6. 添加缓存层

  当前问题: 每次请求都直接调用外部 API，无数据缓存

  建议:
  - 引入 Redis 缓存高频数据
  - 对于不常变化的数据（如项目列表）设置 TTL 缓存
  - 周报数据可缓存到本地文件系统

  from functools import lru_cache

  @lru_cache(maxsize=100, ttl=3600)
  def get_project_info(repo_id: str) -> dict:
      ...

  ---
  7. 完善错误处理机制

  当前问题: 错误处理分散，缺乏统一的异常体系

  建议:
  # exceptions.py
  class MericoBaseException(Exception):
      """基础异常类"""

  class APIRequestError(MericoBaseException):
      """API 请求异常"""

  class ConfigurationError(MericoBaseException):
      """配置异常"""

  class DataProcessingError(MericoBaseException):
      """数据处理异常"""

  # 全局异常处理器
  @app.errorhandler(MericoBaseException)
  def handle_merico_error(error):
      return jsonify({"error": str(error), "code": error.code}), error.status

  ---
  8. 测试体系建设

  当前问题: 测试文件分散，缺乏单元测试

  建议:
  tests/
  ├── unit/                # 单元测试
  │   ├── test_agents.py
  │   ├── test_analyzers.py
  │   └── test_utils.py
  ├── integration/         # 集成测试
  │   └── test_api.py
  ├── fixtures/            # 测试数据
  └── conftest.py          # pytest 配置

  引入 pytest + pytest-cov 进行测试覆盖率统计

  ---
  9. 依赖注入改造

  当前问题: 类之间直接实例化依赖，耦合度高

  建议: 使用依赖注入提升可测试性：

  # 当前方式
  class WeeklyReportGenerator:
      def __init__(self, config):
          self.ai_client = ZhipuAI(config['api_key'])  # 直接耦合

  # 优化后
  class WeeklyReportGenerator:
      def __init__(self, ai_client: AIClientInterface):  # 依赖抽象
          self.ai_client = ai_client

  ---
  10. API 版本管理

  当前问题: API 无版本控制，升级困难

  建议:
  /api/v1/weekly-report/generate
  /api/v1/analysis/uncommented
  /api/v2/...  # 未来版本

  ---
  优先级排序

  | 优先级 | 优化项       | 收益      |
  |-----|-----------|---------|
  | P0  | 合并 Web 服务 | 降低运维复杂度 |
  | P0  | 配置管理优化    | 提升安全性   |
  | P1  | 异步请求改造    | 大幅提升性能  |
  | P1  | 抽象公共层     | 减少重复代码  |
  | P2  | 项目结构重组    | 提升可维护性  |
  | P2  | 错误处理机制    | 增强健壮性   |
  | P3  | 缓存层       | 降低外部依赖  |
  | P3  | 测试体系      | 保障代码质量  |