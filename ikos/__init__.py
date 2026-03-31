"""Ikos - Intelligent Knowledge Building System.

从网络信息到结构化知识 - 多轮 AI 深度挖掘与重构平台。
"""

__version__ = "0.1.0"
__author__ = "jamsyan"
__email__ = "jihanyang123@163.com"

from ikos.core import (
    ModelProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    PlaywrightSearchProvider,
    SearchProvider,
    VoteEngine,
    VotingConfig,
)

__all__ = [
    "ModelProvider",
    "SearchProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "PlaywrightSearchProvider",
    "VoteEngine",
    "VotingConfig",
]
