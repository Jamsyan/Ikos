"""模型缓存管理器 - 管理多来源模型缓存。"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


class ModelCacheManager:
    """模型缓存管理器。"""

    CACHE_ROOT = Path.home() / ".cache" / "ikos"
    MODELS_DIR = CACHE_ROOT / "models"
    TEMP_DIR = CACHE_ROOT / "temp"
    METADATA_FILE = "metadata.json"

    # 清理无用文件，保留核心模型文件
    UNWANTED_PATTERNS = [
        "README.md",
        "README_zh.md",
        "LICENSE",
        "LICENSE.txt",
        "NOTICE",
        ".gitignore",
        "*.git",
        "*.md",
    ]

    # 核心模型文件模式
    ESSENTIAL_PATTERNS = [
        "*.json",
        "*.bin",
        "*.safetensors",
        "*.pt",
        "*.pth",
        "*.onnx",
        "*.txt",
        "*.vocab",
        "*.model",
    ]

    def __init__(self, cache_dir: str | Path | None = None):
        """初始化缓存管理器。"""
        if cache_dir is None:
            self.cache_root = self.CACHE_ROOT
            self.models_dir = self.MODELS_DIR
            self.temp_dir = self.TEMP_DIR
        else:
            self.models_dir = Path(cache_dir)
            self.cache_root = self.models_dir.parent
            self.temp_dir = self.cache_root / "temp"

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info("缓存管理器已初始化，模型目录：{}", self.models_dir)

    def get_source_dir(self, source: str) -> Path:
        """获取指定来源的缓存目录。"""
        source_dir = self.models_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)
        return source_dir

    def get_model_path(
        self,
        model_id: str,
        revision: str = "master",
        source: str = "modelscope",
        create: bool = False,
    ) -> Path:
        """获取模型缓存路径。

        Args:
            model_id: 模型 ID（格式：organization/model_name）
            revision: 版本分支

        Returns:
            Path: 模型缓存路径
        """
        # 解析模型 ID
        parts = model_id.split("/")
        if len(parts) == 2:
            org, model = parts
        else:
            org = "default"
            model = parts[0]

        source_dir = self.get_source_dir(source)

        # 构建路径：models/{source}/{org}/{model}/{revision}
        model_path = source_dir / org / model / revision

        if create:
            model_path.mkdir(parents=True, exist_ok=True)

        return model_path

    def save_metadata(
        self,
        model_path: Path,
        model_id: str,
        revision: str,
        source: str,
        download_info: dict[str, Any] | None = None,
    ) -> None:
        """保存模型元数据。

        Args:
            model_path: 模型路径
            model_id: 模型 ID
            revision: 版本
            download_info: 下载信息
        """
        metadata = {
            "model_id": model_id,
            "revision": revision,
            "downloaded_at": datetime.now().isoformat(),
            "source": source,
            "files_count": 0,
            "total_size": 0,
            "download_info": download_info or {},
        }

        # 统计文件信息
        if model_path.exists():
            files = list(model_path.rglob("*"))
            metadata["files_count"] = len([f for f in files if f.is_file()])
            metadata["total_size"] = sum(f.stat().st_size for f in files if f.is_file())

        # 保存元数据
        metadata_file = model_path / self.METADATA_FILE
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.debug("元数据已保存：{}", metadata_file)

    def load_metadata(self, model_path: Path) -> dict[str, Any]:
        """加载模型元数据。

        Args:
            model_path: 模型路径

        Returns:
            dict: 元数据字典
        """
        metadata_file = model_path / self.METADATA_FILE

        if not metadata_file.exists():
            return {}

        with open(metadata_file, encoding="utf-8") as f:
            return json.load(f)

    def cleanup_unwanted_files(self, model_path: Path) -> int:
        """清理不需要的文件。

        Args:
            model_path: 模型路径

        Returns:
            int: 清理的文件数量
        """
        cleaned_count = 0

        # 遍历所有文件
        for file in model_path.rglob("*"):
            if not file.is_file():
                continue

            # 跳过元数据文件
            if file.name == self.METADATA_FILE:
                continue

            # 检查是否需要清理
            should_remove = False

            for pattern in self.UNWANTED_PATTERNS:
                if pattern.startswith("*"):
                    # 通配符匹配
                    if file.suffix == pattern[1:]:
                        should_remove = True
                        break
                else:
                    # 精确匹配
                    if file.name == pattern:
                        should_remove = True
                        break

            if should_remove:
                try:
                    file.unlink()
                    logger.debug("清理文件：{}", file)
                    cleaned_count += 1
                except Exception as e:
                    logger.warning("清理文件失败 {}: {}", file, e)

        logger.info("清理完成，共清理 {} 个文件", cleaned_count)
        return cleaned_count

    def verify_integrity(self, model_path: Path) -> dict[str, Any]:
        """验证模型完整性。

        Args:
            model_path: 模型路径

        Returns:
            dict: 验证结果
        """
        result = {
            "valid": True,
            "files_count": 0,
            "total_size": 0,
            "essential_files": [],
            "missing_files": [],
            "errors": [],
        }

        if not model_path.exists():
            result["valid"] = False
            result["errors"].append("模型目录不存在")
            return result

        # 统计文件
        files = list(model_path.rglob("*"))
        result["files_count"] = len([f for f in files if f.is_file()])
        result["total_size"] = sum(f.stat().st_size for f in files if f.is_file())

        # 检查核心文件
        has_config = False
        has_model = False

        for pattern in self.ESSENTIAL_PATTERNS:
            matched_files = list(model_path.glob(f"**/{pattern}"))

            if "config" in pattern.lower() or pattern == "*.json":
                if matched_files:
                    has_config = True
                    result["essential_files"].extend([str(f) for f in matched_files[:5]])

            if any(x in pattern.lower() for x in ["bin", "safetensors", "pt", "pth", "onnx"]):
                if matched_files:
                    has_model = True
                    result["essential_files"].extend([str(f) for f in matched_files[:5]])

        # 验证完整性
        if not has_config:
            result["valid"] = False
            result["missing_files"].append("配置文件 (config.json)")

        if not has_model:
            result["valid"] = False
            result["missing_files"].append("模型文件 (*.bin/*.safetensors)")

        return result

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息。

        Returns:
            dict: 统计信息
        """
        stats = {
            "total_models": 0,
            "total_size": 0,
            "models_by_org": {},
            "oldest_model": None,
            "newest_model": None,
        }

        for model_info in self.list_cached_models():
            org_name = model_info.get("name", "unknown").split("/")[0]
            stats["models_by_org"].setdefault(org_name, 0)
            stats["models_by_org"][org_name] += 1
            stats["total_models"] += 1
            stats["total_size"] += int(model_info.get("total_size", 0))

            downloaded_at = model_info.get("downloaded_at")
            if downloaded_at:
                if not stats["oldest_model"] or downloaded_at < stats["oldest_model"][1]:
                    stats["oldest_model"] = (model_info["path"], downloaded_at)
                if not stats["newest_model"] or downloaded_at > stats["newest_model"][1]:
                    stats["newest_model"] = (model_info["path"], downloaded_at)

        return stats

    def list_cached_models(self) -> list[dict[str, Any]]:
        """列出已缓存模型。"""
        models: dict[tuple[str, str, str], dict[str, Any]] = {}

        for metadata_file in self.models_dir.rglob(self.METADATA_FILE):
            model_path = metadata_file.parent
            metadata = self.load_metadata(model_path)
            model_id = metadata.get("model_id")
            revision = metadata.get("revision", "unknown")
            source = metadata.get("source", "unknown")
            if not model_id:
                continue

            key = (model_id, revision, source)
            models[key] = {
                "name": model_id,
                "revision": revision,
                "source": source,
                "path": str(model_path),
                "downloaded_at": metadata.get("downloaded_at", ""),
                "files_count": metadata.get("files_count", 0),
                "total_size": metadata.get("total_size", 0),
            }

        if models:
            return sorted(
                models.values(),
                key=lambda item: item.get("downloaded_at", ""),
                reverse=True,
            )

        return self._discover_legacy_models()

    def find_model_path(self, model_id: str, revision: str | None = "master") -> Path | None:
        """根据元数据查找已缓存模型路径。"""
        for model_info in self.list_cached_models():
            if model_info.get("name") != model_id:
                continue
            if revision is not None and model_info.get("revision") != revision:
                continue

            model_path = Path(model_info["path"])
            if model_path.exists():
                return model_path

        return None

    def _discover_legacy_models(self) -> list[dict[str, Any]]:
        """兜底扫描旧缓存目录。"""
        candidates: dict[str, dict[str, Any]] = {}
        for config_file in self.models_dir.rglob("config.json"):
            model_path = config_file.parent
            if not any(model_path.glob(pattern) for pattern in ("*.safetensors", "*.bin")):
                continue

            model_name = self._infer_model_name(model_path)
            candidates[str(model_path)] = {
                "name": model_name,
                "revision": "unknown",
                "source": self._infer_source(model_path),
                "path": str(model_path),
                "downloaded_at": "",
                "files_count": len([file for file in model_path.rglob("*") if file.is_file()]),
                "total_size": sum(
                    file.stat().st_size for file in model_path.rglob("*") if file.is_file()
                ),
            }

        return sorted(candidates.values(), key=lambda item: item["name"])

    def _infer_model_name(self, model_path: Path) -> str:
        """根据目录结构推断模型名。"""
        parts = list(model_path.parts)
        if "modelscope" in parts:
            index = parts.index("modelscope")
            if len(parts) >= index + 4:
                return f"{parts[index + 1]}/{parts[index + 2]}"

        for part in reversed(parts):
            if part.startswith("models--"):
                return part.replace("models--", "").replace("--", "/")

        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"

        return model_path.name

    def _infer_source(self, model_path: Path) -> str:
        """根据目录结构推断来源。"""
        parts = set(model_path.parts)
        if "modelscope" in parts:
            return "modelscope"
        if "huggingface" in parts:
            return "huggingface"
        return "unknown"

    def clear_cache(self, model_id: str | None = None, older_than_days: int | None = None) -> int:
        """清除缓存。

        Args:
            model_id: 指定模型 ID（None 表示清除所有）
            older_than_days: 清除超过指定天数的模型

        Returns:
            int: 清理的模型数量
        """
        cleaned_count = 0

        if model_id:
            model_path = self.find_model_path(model_id, revision=None)
            if model_path and model_path.exists():
                shutil.rmtree(model_path)
                logger.info("已清除模型：{}", model_id)
                cleaned_count = 1
        elif older_than_days:
            # 清除旧模型
            cutoff_date = datetime.now().timestamp() - (older_than_days * 86400)

            for org_dir in self.models_dir.iterdir():
                if not org_dir.is_dir():
                    continue

                for model_dir in org_dir.iterdir():
                    if not model_dir.is_dir():
                        continue

                    for revision_dir in model_dir.iterdir():
                        if not revision_dir.is_dir():
                            continue

                        metadata = self.load_metadata(revision_dir)
                        if metadata:
                            downloaded_at = metadata.get("downloaded_at")
                            if downloaded_at:
                                try:
                                    download_time = datetime.fromisoformat(
                                        downloaded_at
                                    ).timestamp()
                                    if download_time < cutoff_date:
                                        shutil.rmtree(revision_dir)
                                        logger.info("清除旧模型：{}", revision_dir)
                                        cleaned_count += 1
                                except Exception as e:
                                    logger.warning("解析时间失败：{}", e)
        else:
            # 清除所有
            if self.models_dir.exists():
                shutil.rmtree(self.models_dir)
                self.models_dir.mkdir(parents=True, exist_ok=True)
                logger.info("已清除所有模型缓存")
                cleaned_count = -1  # -1 表示全部清除

        return cleaned_count

    def print_stats(self) -> None:
        """打印缓存统计信息。"""
        stats = self.get_cache_stats()

        logger.info("=" * 60)
        logger.info("缓存统计")
        logger.info("=" * 60)
        logger.info("总模型数：{}", stats["total_models"])
        logger.info("总大小：{}", self._format_size(stats["total_size"]))
        logger.info("按组织统计:")
        for org, count in stats["models_by_org"].items():
            logger.info("  {}: {} 个模型", org, count)

        if stats["oldest_model"]:
            logger.info("最早下载：{}", stats["oldest_model"][0])
            logger.info("  时间：{}", stats["oldest_model"][1])

        if stats["newest_model"]:
            logger.info("最近下载：{}", stats["newest_model"][0])
            logger.info("  时间：{}", stats["newest_model"][1])

        logger.info("=" * 60)

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小。

        Args:
            size_bytes: 字节数

        Returns:
            str: 格式化后的大小
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


# 全局缓存管理器实例
_global_cache_manager: ModelCacheManager | None = None


def get_cache_manager(cache_dir: str | Path | None = None) -> ModelCacheManager:
    """获取缓存管理器（单例模式）。

    Args:
        cache_dir: 自定义缓存目录

    Returns:
        ModelCacheManager: 缓存管理器实例
    """
    global _global_cache_manager

    if _global_cache_manager is None or (
        cache_dir and _global_cache_manager.cache_root != Path(cache_dir)
    ):
        _global_cache_manager = ModelCacheManager(cache_dir)

    return _global_cache_manager
