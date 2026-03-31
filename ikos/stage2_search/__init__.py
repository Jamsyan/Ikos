"""第二阶段：智能检索机制。

接收工程化提示词，通过多模型投票拆分任务、并行搜索发现、备忘录迭代评审，最终产出海量原始网络数据。

核心机制：
- 多模型拆分
- 多品审核
- 单决策
- 备忘录迭代评审
"""

from .memo import MemoManager
from .searcher import SearchExecutor
from .task_splitter import TaskSplitter

__all__ = [
    "TaskSplitter",
    "SearchExecutor",
    "MemoManager",
]
