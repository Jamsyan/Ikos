"""模型源选择器 - 智能选择魔塔社区或 Hugging Face."""

import socket
from typing import Literal
from loguru import logger

ModelSourceType = Literal["modelscope", "huggingface", "auto"]


class ModelSourceSelector:
    """模型源选择器。
    
    根据网络环境自动选择最优的模型源：
    - 魔塔社区（ModelScope）- 国内推荐
    - Hugging Face - 国际推荐
    """
    
    # 魔塔社区检测域名
    MODELSCOPE_HOST = "www.modelscope.cn"
    
    # Hugging Face 检测域名
    HUGGINGFACE_HOST = "huggingface.co"
    
    def __init__(self, preferred: ModelSourceType = "auto"):
        """初始化模型源选择器。
        
        Args:
            preferred: 首选模型源（auto/modelscope/huggingface）
        """
        self.preferred = preferred
        self._cached_result: ModelSourceType | None = None
    
    def detect(self) -> ModelSourceType:
        """检测并选择最优模型源。
        
        Returns:
            ModelSourceType: 选择的模型源
        """
        # 如果指定了具体源，直接返回
        if self.preferred != "auto":
            logger.info(f"使用指定的模型源：{self.preferred}")
            return self.preferred
        
        # 使用缓存结果
        if self._cached_result:
            logger.debug(f"使用缓存的模型源：{self._cached_result}")
            return self._cached_result
        
        # 自动检测
        result = self._auto_detect()
        self._cached_result = result
        
        return result
    
    def _auto_detect(self) -> ModelSourceType:
        """自动检测网络环境并选择模型源。
        
        检测逻辑：
        1. 优先尝试连接魔塔社区
        2. 如果魔塔不可用，尝试 Hugging Face
        3. 都不可用时，返回 modelscope（作为默认）
        
        Returns:
            ModelSourceType: 选择的模型源
        """
        logger.info("开始自动检测模型源...")
        
        # 检测魔塔社区
        modelscope_available = self._check_host(self.MODELSCOPE_HOST)
        if modelscope_available:
            logger.info("✅ 魔塔社区可访问，使用魔塔社区")
            return "modelscope"
        
        # 检测 Hugging Face
        huggingface_available = self._check_host(self.HUGGINGFACE_HOST)
        if huggingface_available:
            logger.info("✅ Hugging Face 可访问，使用 Hugging Face")
            return "huggingface"
        
        # 都不可用，返回默认（魔塔）
        logger.warning("⚠️  两个模型源都不可访问，默认使用魔塔社区")
        return "modelscope"
    
    def _check_host(self, host: str, port: int = 443, timeout: float = 3.0) -> bool:
        """检查主机是否可访问。
        
        Args:
            host: 主机名
            port: 端口号（默认 443 HTTPS）
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否可访问
        """
        try:
            # 使用 socket 检测连接
            socket.setdefaulttimeout(timeout)
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error, OSError) as e:
            logger.debug(f"主机 {host} 不可访问：{e}")
            return False
    
    def get_download_url(
        self,
        model_id: str,
        revision: str = "master"
    ) -> str:
        """获取模型下载 URL。
        
        Args:
            model_id: 模型 ID
            revision: 版本分支
            
        Returns:
            str: 下载 URL
        """
        source = self.detect()
        
        if source == "modelscope":
            return f"https://www.modelscope.cn/models/{model_id}/files"
        else:
            return f"https://huggingface.co/{model_id}/tree/{revision}"
    
    def get_api_endpoint(self) -> str:
        """获取 API 端点。
        
        Returns:
            str: API 端点 URL
        """
        source = self.detect()
        
        if source == "modelscope":
            return "https://www.modelscope.cn/api/v1"
        else:
            return "https://huggingface.co/api"
    
    def reset_cache(self) -> None:
        """重置缓存结果。"""
        self._cached_result = None
        logger.info("模型源缓存已重置")


# 全局选择器实例
_global_selector: ModelSourceSelector | None = None


def get_model_source(preferred: ModelSourceType = "auto") -> ModelSourceType:
    """获取模型源（便捷函数）。
    
    Args:
        preferred: 首选模型源
        
    Returns:
        ModelSourceType: 选择的模型源
    """
    global _global_selector
    
    if _global_selector is None or _global_selector.preferred != preferred:
        _global_selector = ModelSourceSelector(preferred)
    
    return _global_selector.detect()


def is_modelscope(preferred: ModelSourceType = "auto") -> bool:
    """判断是否使用魔塔社区。
    
    Args:
        preferred: 首选模型源
        
    Returns:
        bool: 是否使用魔塔社区
    """
    return get_model_source(preferred) == "modelscope"


def is_huggingface(preferred: ModelSourceType = "auto") -> bool:
    """判断是否使用 Hugging Face。
    
    Args:
        preferred: 首选模型源
        
    Returns:
        bool: 是否使用 Hugging Face
    """
    return get_model_source(preferred) == "huggingface"
