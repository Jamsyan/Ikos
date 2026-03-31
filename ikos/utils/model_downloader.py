"""模型下载器 - 专注魔塔社区，集成缓存管理."""

from pathlib import Path
from typing import Any

from loguru import logger

from .cache_manager import ModelCacheManager
from .model_source import ModelSourceSelector, ModelSourceType


class ModelDownloadError(RuntimeError):
    """包装下载上下文，便于 UI 直接展示诊断信息。"""

    def __init__(
        self,
        model_id: str,
        source: str,
        revision: str,
        cache_dir: Path,
        reason: str,
    ):
        self.model_id = model_id
        self.source = source
        self.revision = revision
        self.cache_dir = cache_dir
        self.reason = reason
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        lines = [
            f"模型: {self.model_id}",
            f"来源: {self.source}",
            f"版本: {self.revision}",
            f"缓存目录: {self.cache_dir}",
            f"失败原因: {self.reason}",
        ]

        lowered = self.reason.lower()
        if "10060" in lowered or "connecttimeout" in lowered or "timed out" in lowered:
            lines.append(
                "建议: 当前更像是网络或代理问题，请检查目标源连通性，必要时切换镜像或代理。"
            )

        return "\n".join(lines)


class ModelDownloader:
    """模型下载器。

    专注魔塔社区模型下载，集成缓存管理：
    - 自动清理无用文件（README/LICENSE 等）
    - 版本管理
    - 完整性验证
    - 空间统计
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        preferred_source: ModelSourceType = "auto",
        allow_fallback: bool = False,
    ):
        """初始化模型下载器。

        Args:
            cache_dir: 模型缓存目录
            preferred_source: 首选模型源
        """
        # 使用缓存管理器
        self.cache_manager = ModelCacheManager(cache_dir)
        self.cache_dir = self.cache_manager.models_dir
        self.source_selector = ModelSourceSelector(preferred_source)
        self.allow_fallback = allow_fallback

        logger.info("模型下载器已初始化")
        logger.info("缓存目录：{}", self.cache_dir)
        logger.info("首选模型源：{}", preferred_source)
        logger.info("失败后自动回退：{}", "开启" if allow_fallback else "关闭")

    def download(
        self,
        model_id: str,
        revision: str = "master",
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        resume_download: bool = True,
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

        logger.info("开始下载模型：{}", model_id)
        logger.info("使用模型源：{}", source)

        sources = [source]
        if self.allow_fallback:
            fallback = "huggingface" if source == "modelscope" else "modelscope"
            sources.append(fallback)

        last_error: ModelDownloadError | None = None
        for current_source in sources:
            try:
                resolved_revision = self._resolve_revision(current_source, revision)
                if resolved_revision != revision:
                    logger.info(
                        "已按 {} 规则调整版本：{} -> {}",
                        current_source,
                        revision,
                        resolved_revision,
                    )
                if current_source == "modelscope":
                    return self._download_from_modelscope(
                        model_id,
                        resolved_revision,
                        allow_patterns,
                        ignore_patterns,
                        resume_download,
                    )

                return self._download_from_huggingface(
                    model_id, resolved_revision, allow_patterns, ignore_patterns, resume_download
                )
            except ModelDownloadError as exc:
                last_error = exc
                if current_source != sources[-1]:
                    logger.warning("来源 {} 下载失败，准备尝试下一个来源", current_source)

        assert last_error is not None
        raise last_error

    def _resolve_revision(self, source: str, revision: str) -> str:
        """按来源修正默认 revision。"""
        if source == "modelscope" and revision == "main":
            return "master"
        if source == "huggingface" and revision == "master":
            return "main"
        return revision

    def _download_from_modelscope(
        self,
        model_id: str,
        revision: str,
        allow_patterns: list[str] | None,
        ignore_patterns: list[str] | None,
        resume_download: bool,
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

            source_dir = self.cache_manager.get_source_dir("modelscope")
            logger.info("使用魔塔社区下载：{}", model_id)
            logger.info("目标版本：{}", revision)
            logger.info("开始拉取模型文件...")

            # 构建下载参数
            download_kwargs = {
                "model_id": model_id,
                "revision": revision,
                "cache_dir": str(source_dir),
            }

            if allow_patterns:
                download_kwargs["allow_patterns"] = allow_patterns
            if ignore_patterns:
                download_kwargs["ignore_patterns"] = ignore_patterns

            # 执行下载
            downloaded_path = snapshot_download(**download_kwargs)
            downloaded_path = Path(downloaded_path)

            logger.info("模型下载完成：{}", downloaded_path)

            # 清理无用文件
            logger.info("清理无用文件（README/LICENSE 等）...")
            cleaned_count = self.cache_manager.cleanup_unwanted_files(downloaded_path)
            logger.info("清理了 {} 个文件", cleaned_count)

            # 验证完整性
            logger.info("验证模型完整性...")
            integrity = self.cache_manager.verify_integrity(downloaded_path)

            if integrity["valid"]:
                logger.info("模型完整性验证通过")
                logger.info("  文件数：{}", integrity["files_count"])
                logger.info(
                    "  总大小：{}", self.cache_manager._format_size(integrity["total_size"])
                )
                logger.info("  核心文件：{} 个", len(integrity["essential_files"]))
            else:
                logger.warning("模型完整性验证失败")
                for missing in integrity["missing_files"]:
                    logger.warning("  缺失：{}", missing)

            # 保存元数据
            self.cache_manager.save_metadata(
                downloaded_path,
                model_id,
                revision,
                source="modelscope",
                download_info={
                    "source": "modelscope",
                    "cleaned_files": cleaned_count,
                    "integrity": integrity,
                },
            )

            return downloaded_path

        except ImportError:
            logger.error("modelscope 库未安装，请运行：uv add modelscope")
            raise
        except Exception as e:
            logger.error("从魔塔社区下载失败：{}", e)
            raise ModelDownloadError(
                model_id=model_id,
                source="modelscope",
                revision=revision,
                cache_dir=self.cache_manager.get_source_dir("modelscope"),
                reason=str(e),
            ) from e

    def _download_from_huggingface(
        self,
        model_id: str,
        revision: str,
        allow_patterns: list[str] | None,
        ignore_patterns: list[str] | None,
        resume_download: bool,
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

            source_dir = self.cache_manager.get_source_dir("huggingface")
            logger.info("使用 Hugging Face 下载：{}", model_id)
            logger.info("目标版本：{}", revision)
            logger.info("开始拉取模型文件...")

            # 构建下载参数
            download_kwargs = {
                "repo_id": model_id,
                "revision": revision,
                "cache_dir": str(source_dir),
                "resume_download": resume_download,
            }

            if allow_patterns:
                download_kwargs["allow_patterns"] = allow_patterns
            if ignore_patterns:
                download_kwargs["ignore_patterns"] = ignore_patterns

            # 执行下载
            model_dir = snapshot_download(**download_kwargs)
            downloaded_path = Path(model_dir)

            self.cache_manager.save_metadata(
                downloaded_path,
                model_id,
                revision,
                source="huggingface",
                download_info={
                    "source": "huggingface",
                    "allow_patterns": allow_patterns or [],
                    "ignore_patterns": ignore_patterns or [],
                },
            )

            logger.info("模型下载完成：{}", downloaded_path)
            return downloaded_path

        except ImportError:
            logger.error("huggingface_hub 库未安装，请运行：uv add huggingface_hub")
            raise
        except Exception as e:
            logger.error("从 Hugging Face 下载失败：{}", e)
            raise ModelDownloadError(
                model_id=model_id,
                source="huggingface",
                revision=revision,
                cache_dir=self.cache_manager.get_source_dir("huggingface"),
                reason=str(e),
            ) from e

    def get_model_path(self, model_id: str, revision: str = "master") -> Path | None:
        """获取模型本地路径（如果已缓存）。

        Args:
            model_id: 模型 ID
            revision: 版本

        Returns:
            Path | None: 模型路径，不存在则返回 None
        """
        cache_path = self.cache_manager.find_model_path(model_id, revision)
        if cache_path:
            logger.info("模型已缓存：{}", cache_path)
        return cache_path

    def clear_cache(self, model_id: str | None = None) -> None:
        """清除模型缓存。

        Args:
            model_id: 模型 ID（None 表示清除所有）
        """
        if model_id:
            cache_path = self.cache_manager.find_model_path(model_id, revision=None)
            if cache_path and cache_path.exists():
                import shutil

                shutil.rmtree(cache_path)
                logger.info("已清除模型缓存：{}", model_id)
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
    **kwargs: Any,
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
