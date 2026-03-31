"""第一阶段：需求解析机制。

将用户的自然语言输入，通过多轮转换与验证，最终输出工程化提示词。

核心机制：
- 多轮转换
- 旁系监督
- 网络验证
- 球形知识空间构建
"""

from .parser import RequirementParser
from .supervisor import SideSupervisor
from .validator import NetworkValidator

__all__ = [
    "RequirementParser",
    "NetworkValidator",
    "SideSupervisor",
]
