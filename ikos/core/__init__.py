"""Core abstractions and interfaces for Ikos.

包含核心抽象接口：
- ModelProvider: 多模型统一调用接口
- SearchProvider: 搜索引擎抽象接口
- VoteEngine: 多模型投票引擎
"""

from .model_provider import ModelProvider
from .search_provider import SearchProvider, PlaywrightSearchProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAICompatibleProvider
from .vote_engine import VoteEngine, VotingConfig

__all__ = [
    "ModelProvider",
    "SearchProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "PlaywrightSearchProvider",
    "VoteEngine",
    "VotingConfig",
]
