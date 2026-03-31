"""第四阶段：输出分流机制。

接收结构化数据和知识图谱，根据用户配置分流到不同输出路径，最终产出用户所需的文件或数据库记录。

核心机制：
- 用户配置
- 模板输出
- 抄成熟方案
"""

from .db_output import DatabaseOutputter
from .dispatcher import OutputDispatcher
from .file_output import FileOutputter

__all__ = [
    "OutputDispatcher",
    "FileOutputter",
    "DatabaseOutputter",
]
