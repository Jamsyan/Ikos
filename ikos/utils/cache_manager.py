"""模型缓存管理器 - 专注魔塔社区。"""

import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any
from loguru import logger


class ModelCacheManager:
    """魔塔社区模型缓存管理器。"""
    
    CACHE_ROOT = Path.home() / ".cache" / "ikos"
    MODELS_DIR = CACHE_ROOT / "models" / "modelscope"
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
        self.cache_root = Path(cache_dir) if cache_dir else self.CACHE_ROOT
        self.models_dir = self.cache_root / "models" / "modelscope"
        self.temp_dir = self.cache_root / "temp"
        
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("缓存管理器已初始化，目录：%s", self.cache_root)
    
    def get_model_path(
        self,
        model_id: str,
        revision: str = "master"
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
        
        # 构建路径：models/modelscope/{org}/{model}/{revision}
        model_path = self.models_dir / org / model / revision
        
        # 确保目录存在
        model_path.mkdir(parents=True, exist_ok=True)
        
        return model_path
    
    def save_metadata(
        self,
        model_path: Path,
        model_id: str,
        revision: str,
        download_info: dict[str, Any] | None = None
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
            "source": "modelscope",
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
        
        logger.debug("元数据已保存：{metadata_file}")
    
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
        
        with open(metadata_file, "r", encoding="utf-8") as f:
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
                    logger.debug("清理文件：{file}")
                    cleaned_count += 1
                except Exception as e:
                    logger.warning("清理文件失败 {file}: {e}")
        
        logger.info("清理完成，共清理 {cleaned_count} 个文件")
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
            "errors": []
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
        
        if not self.models_dir.exists():
            return stats
        
        # 遍历所有模型
        for org_dir in self.models_dir.iterdir():
            if not org_dir.is_dir():
                continue
            
            org_name = org_dir.name
            stats["models_by_org"][org_name] = 0
            
            for model_dir in org_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                
                stats["total_models"] += 1
                stats["models_by_org"][org_name] += 1
                
                # 计算大小
                for revision_dir in model_dir.iterdir():
                    if revision_dir.is_dir():
                        size = sum(f.stat().st_size for f in revision_dir.rglob("*") if f.is_file())
                        stats["total_size"] += size
                        
                        # 检查元数据
                        metadata = self.load_metadata(revision_dir)
                        if metadata:
                            downloaded_at = metadata.get("downloaded_at")
                            if downloaded_at:
                                if not stats["oldest_model"] or downloaded_at < stats["oldest_model"][1]:
                                    stats["oldest_model"] = (str(revision_dir), downloaded_at)
                                if not stats["newest_model"] or downloaded_at > stats["newest_model"][1]:
                                    stats["newest_model"] = (str(revision_dir), downloaded_at)
        
        return stats
    
    def clear_cache(
        self,
        model_id: str | None = None,
        older_than_days: int | None = None
    ) -> int:
        """清除缓存。
        
        Args:
            model_id: 指定模型 ID（None 表示清除所有）
            older_than_days: 清除超过指定天数的模型
            
        Returns:
            int: 清理的模型数量
        """
        cleaned_count = 0
        
        if model_id:
            # 清除指定模型
            model_path = self.get_model_path(model_id)
            if model_path.exists():
                shutil.rmtree(model_path)
                logger.info("已清除模型：{model_id}")
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
                                    download_time = datetime.fromisoformat(downloaded_at).timestamp()
                                    if download_time < cutoff_date:
                                        shutil.rmtree(revision_dir)
                                        logger.info("清除旧模型：{revision_dir}")
                                        cleaned_count += 1
                                except Exception as e:
                                    logger.warning("解析时间失败：{e}")
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
        
        print("\n" + "=" * 60)
        print("📊 缓存统计")
        print("=" * 60)
        print(f"总模型数：{stats['total_models']}")
        print(f"总大小：{self._format_size(stats['total_size'])}")
        print(f"\n按组织统计:")
        for org, count in stats['models_by_org'].items():
            print(f"  {org}: {count} 个模型")
        
        if stats['oldest_model']:
            print(f"\n最早下载：{stats['oldest_model'][0]}")
            print(f"  时间：{stats['oldest_model'][1]}")
        
        if stats['newest_model']:
            print(f"\n最近下载：{stats['newest_model'][0]}")
            print(f"  时间：{stats['newest_model'][1]}")
        
        print("=" * 60 + "\n")
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小。
        
        Args:
            size_bytes: 字节数
            
        Returns:
            str: 格式化后的大小
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
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
    
    if _global_cache_manager is None or (cache_dir and _global_cache_manager.cache_root != Path(cache_dir)):
        _global_cache_manager = ModelCacheManager(cache_dir)
    
    return _global_cache_manager
