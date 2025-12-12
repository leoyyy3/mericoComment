 重复函数分析失败: 'OutputConfig' object has no attribute 'save_raw'
Traceback (most recent call last):
  File "/Users/leoyang/Documents/langchainAgents/mericoComment/src/services/analysis_service.py", line 78, in run_duplicate_analysis
    with DuplicateFunctionsFetcher(settings=self.settings) as fetcher:
         ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/leoyang/Documents/langchainAgents/mericoComment/src/core/fetchers/duplicate_fetcher.py", line 32, in __init__
    self._init_from_settings(settings)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/Users/leoyang/Documents/langchainAgents/mericoComment/src/core/fetchers/duplicate_fetcher.py", line 53, in _init_from_settings
    'save_raw': settings.output.save_raw,
                ^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'OutputConfig' object has no attribute 'save_raw'