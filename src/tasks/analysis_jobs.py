"""
  分析类异步任务

  注意：这些函数会在 Worker 进程中执行，不是在 Flask 进程中
  """
from pathlib import Path
from src.utils import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def analyze_uncommented(repo_path: str = None, options: dict = None) -> dict:
    """
    分析未注释函数
    
    Args:
        repo_path: 仓库路径/ID。如果为 None，则执行批量分析。
        options: 可选配置 (token 等)
        
    Returns:
        分析结果字典
    """
    logger.info(f"后台任务：开始分析未注释函数 (repo_path: {repo_path})")

    try:
        from src.core.agents import UncommentedFunctionsAgent
        from config.settings import get_settings
        
        settings = get_settings()
        token = options.get('token') if options else None
        
        with UncommentedFunctionsAgent(settings=settings, token=token) as agent:
            if repo_path:
                result = agent.analyze(repo_path)
            else:
                result = agent.run()

        uncommented_count = result.get('summary', {}).get('total_uncommented_functions', 0)
        logger.info(f"分析完成，发现 {uncommented_count} 个未注释函数")

        return {
            'status': 'success',
            'data': result,
            'repo_path': repo_path
        }

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        raise  # 抛出异常让 RQ 记录失败状态


def analyze_duplicate(repo_path: str = None, options: dict = None) -> dict:
    """
    分析重复代码
    """
    logger.info(f"后台任务：开始分析重复代码 (repo_path: {repo_path})")

    try:
        from src.core.fetchers import DuplicateFunctionsFetcher
        from config.settings import get_settings
        
        settings = get_settings()
        token = options.get('token') if options else None

        with DuplicateFunctionsFetcher(settings=settings, token=token) as fetcher:
            if repo_path:
                result = fetcher.analyze(repo_path)
            else:
                result = fetcher.run()

        logger.info("重复代码分析完成")

        return {
            'status': 'success',
            'data': result,
            'repo_path': repo_path
        }

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        raise


def analyze_all(repo_path: str = None, options: dict = None) -> dict:
    """
    执行全部分析
    """
    logger.info(f"后台任务：开始全量分析 (repo_path: {repo_path})")

    results = {
        'repo_path': repo_path,
        'uncommented': None,
        'duplicate': None,
    }

    try:
        results['uncommented'] = analyze_uncommented(repo_path, options)
    except Exception as e:
        results['uncommented'] = {'status': 'error', 'message': str(e)}

    try:
        results['duplicate'] = analyze_duplicate(repo_path, options)
    except Exception as e:
        results['duplicate'] = {'status': 'error', 'message': str(e)}

    return results