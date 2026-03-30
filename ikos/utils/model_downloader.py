"""模型下载器 - 支持魔塔社区和 Hugging Face."""

import os
from pathlib import Path
from typing import Any
from loguru import logger

from .model_source import ModelSourceSelector, ModelSourceType


class ModelDownloader:
    """模型下载器。
    
    支持从魔塔社区或 Hugging Face 下载模型，
    自动选择最优源，支持断点续传。
    """
    
    def __init__(
        self,
        cache_dir: str | Path | None = None,
        preferred_source: ModelSourceType = "auto"
    ):
        """初始化模型下载器。
        
        Args:
            cache_dir: 模型缓存目录
            preferred_source: 首选模型源
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "ikos" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.source_selector = ModelSourceSelector(preferred_source)
        
        logger.info(f"模型下载器已初始化")
        logger.info(f"缓存目录：{self.cache_dir}")
        logger.info(f"首选模型源：{preferred_source}")
    
    def download(
        self,
        model_id: str,
        revision: str = "master",
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        resume_download: bool = True
    ) -> Path:
        """下载模型。
        
        Args:
            model_id: 模型 ID
                - 魔塔社区格式：damo/nlp_csanmt_translationzh2en
                - Hugging Face 格式：facebook/bart-base
            revision: 版本分支或 tag
            allow_patterns: 允许下载的文件模式
            ignore_patterns: 忽略的文件模式
            resume_download: 是否支持断点续传
            
        Returns:
            Path: 模型本地路径
        """
        source = self.source_selector.detect()
        
        logger.info(f"开始下载模型：{model_id}")
        logger.info(f"使用模型源：{source}")
        
        if source == "modelscope":
            return self._download_from_modelscope(
                model_id, revision, allow_patterns, ignore_patterns, resume_download
            )
        else:
            return self._download_from_huggingface(
                model_id, revision, allow_patterns, ignore_patterns, resume_download
            )
    
    def _download_from_modelscope(
        self,
        model_id: str,
        revision: str,
        allow_patterns: list[str] | None,
        ignore_patterns: list[str] | None,
        resume_download: bool
    ) -> Path:
        """从魔塔社区下载模型。
        
        Args:
            model_id: 模型 ID
            revision: 版本
            allow_patterns: 允许的文件模式
            ignore_patterns: 忽略的文件模式
            resume_download: 断点续传
            
        Returns:
            Path: 模型本地路径
        """
        try:
            from modelscope import snapshot_download
            
            logger.info(f"使用魔塔社区下载：{model_id}")
            
            # 构建下载参数
            download_kwargs = {
                "model_id": model_id,
                "revision": revision,
                "cache_dir": str(self.cache_dir),
            }
            
            if allow_patterns:
                download_kwargs["include"] = allow_patterns
            if ignore_patterns:
                download_kwargs["exclude"] = ignore_patterns
            
            # 执行下载
            model_dir = snapshot_download(**download_kwargs)
            
            logger.info(f"模型下载完成：{model_dir}")
            return Path(model_dir)
            
        except ImportError:
            logger.error("modelscope 库未安装，请运行：pip install modelscope")
            raise
        except Exception as e:
            logger.error(f"从魔塔社区下载失败：{e}")
            # 尝试切换到 Hugging Face
            logger.info("尝试切换到 Hugging Face 下载...")
            return self._download_from_huggingface(
                model_id, revision, allow_patterns, ignore_patterns, resume_download
            )
    
    def _download_from_huggingface(
        self,
        model_id: str,
        revision: str,
        allow_patterns: list[str] | None,
        ignore_patterns: list[str] | None,
        resume_download: bool
    ) -> Path:
        """从 Hugging Face 下载模型。
        
        Args:
            model_id: 模型 ID
            revision: 版本
            allow_patterns: 允许的文件模式
            ignore_patterns: 忽略的文件模式
            resume_download: 断点续传
            
        Returns:
            Path: 模型本地路径
        """
        try:
            from huggingface_hub import snapshot_download
            
            logger.info(f"使用 Hugging Face 下载：{model_id}")
            
            # 构建下载参数
            download_kwargs = {
                "repo_id": model_id,
                "revision": revision,
                "cache_dir": str(self.cache_dir),
                "resume_download": resume_download,
            }
            
            if allow_patterns:
                download_kwargs["allow_patterns"] = allow_patterns
            if ignore_patterns:
                download_kwargs["ignore_patterns"] = ignore_patterns
            
            # 执行下载
            model_dir = snapshot_download(**download_kwargs)
            
            logger.info(f"模型下载完成：{model_dir}")
            return Path(model_dir)
            
        except ImportError:
            logger.error("huggingface_hub 库未安装，请运行：pip install huggingface_hub")
            raise
        except Exception as e:
            logger.error(f"从 Hugging Face 下载失败：{e}")
            raise
    
    def get_model_path(self, model_id: str, revision: str = "master") -> Path | None:
        """获取模型本地路径（如果已缓存）。
        
        Args:
            model_id: 模型 ID
            revision: 版本
            
        Returns:
            Path | None: 模型路径，不存在则返回 None
        """
        # 检查缓存
        source = self.source_selector.detect()
        
        if source == "modelscope":
            cache_path = self.cache_dir / "models" / model_id.replace("/", "---")
        else:
            cache_path = self.cache_dir / f"models--{model_id.replace('/', '--')}"
        
        if cache_path.exists():
            logger.info(f"模型已缓存：{cache_path}")
            return cache_path
        
        return None
    
    def clear_cache(self, model_id: str | None = None) -> None:
        """清除模型缓存。
        
        Args:
            model_id: 模型 ID（None 表示清除所有）
        """
        if model_id:
            # 清除指定模型
            cache_path = self.cache_dir / f"models--{model_id.replace('/', '--')}"
            if cache_path.exists():
                import shutil
                shutil.rmtree(cache_path)
                logger.info(f"已清除模型缓存：{model_id}")
        else:
            # 清除所有缓存
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("已清除所有模型缓存")


def download_model(
    model_id: str,
    cache_dir: str | Path | None = None,
    preferred_source: ModelSourceType = "auto",
    **kwargs: Any
) -> Path:
    """便捷函数：下载模型。
    
    Args:
        model_id: 模型 ID
        cache_dir: 缓存目录
        preferred_source: 首选模型源
        **kwargs: 其他参数传递给 ModelDownloader.download
        
    Returns:
        Path: 模型本地路径
    """
    downloader = ModelDownloader(cache_dir, preferred_source)
    return downloader.download(model_id, **kwargs)
