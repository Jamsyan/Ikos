"""缓存管理命令行工具."""

import sys
import argparse
from pathlib import Path

from .cache_manager import ModelCacheManager


def cmd_stats(args):
    """显示缓存统计信息。"""
    manager = ModelCacheManager(args.cache_dir)
    manager.print_stats()


def cmd_list(args):
    """列出所有缓存的模型。"""
    manager = ModelCacheManager(args.cache_dir)
    
    if not manager.models_dir.exists():
        print("缓存为空")
        return
    
    print("\n缓存的模型列表:")
    print("=" * 80)
    
    for org_dir in manager.models_dir.iterdir():
        if not org_dir.is_dir():
            continue
        
        org_name = org_dir.name
        
        for model_dir in org_dir.iterdir():
            if not model_dir.is_dir():
                continue
            
            model_name = model_dir.name
            
            for revision_dir in model_dir.iterdir():
                if not revision_dir.is_dir():
                    continue
                
                revision = revision_dir.name
                metadata = manager.load_metadata(revision_dir)
                
                size = sum(f.stat().st_size for f in revision_dir.rglob("*") if f.is_file())
                size_str = manager._format_size(size)
                
                downloaded = metadata.get("downloaded_at", "未知")
                
                print(f"{org_name}/{model_name}@{revision}")
                print(f"  路径：{revision_dir}")
                print(f"  大小：{size_str}")
                print(f"  下载时间：{downloaded}")
                print()
    
    print("=" * 80)


def cmd_clean(args):
    """清理缓存。"""
    manager = ModelCacheManager(args.cache_dir)
    
    if args.model:
        # 清理指定模型
        print(f"清理模型：{args.model}")
        count = manager.clear_cache(model_id=args.model)
        print(f"已清理 {count} 个模型")
    elif args.days:
        # 清理旧模型
        print(f"清理 {args.days} 天前的模型")
        count = manager.clear_cache(older_than_days=args.days)
        print(f"已清理 {count} 个模型")
    elif args.all:
        # 清理所有
        confirm = input("确定要清理所有缓存吗？[y/N]: ")
        if confirm.lower() == 'y':
            count = manager.clear_cache()
            print("已清理所有缓存")
        else:
            print("已取消")
    else:
        print("请指定清理选项：--model, --days, 或 --all")


def cmd_verify(args):
    """验证模型完整性。"""
    manager = ModelCacheManager(args.cache_dir)
    
    if not args.model:
        print("请指定模型 ID: --model <model_id>")
        return
    
    model_path = manager.get_model_path(args.model, args.revision or "master")
    
    if not model_path.exists():
        print(f"模型不存在：{model_path}")
        return
    
    print(f"验证模型：{args.model}@{args.revision or 'master'}")
    print(f"路径：{model_path}")
    print()
    
    integrity = manager.verify_integrity(model_path)
    
    if integrity["valid"]:
        print("✅ 完整性验证通过")
    else:
        print("❌ 完整性验证失败")
        for missing in integrity["missing_files"]:
            print(f"  缺失：{missing}")
        for error in integrity["errors"]:
            print(f"  错误：{error}")
    
    print(f"\n文件数：{integrity['files_count']}")
    print(f"总大小：{manager._format_size(integrity['total_size'])}")
    print(f"核心文件：{len(integrity['essential_files'])} 个")


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(
        description="Ikos 模型缓存管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看缓存统计
  ikos-cache stats
  
  # 列出所有模型
  ikos-cache list
  
  # 清理指定模型
  ikos-cache clean --model damo/nlp_csanmt_translationzh2en
  
  # 清理 30 天前的模型
  ikos-cache clean --days 30
  
  # 清理所有缓存
  ikos-cache clean --all
  
  # 验证模型完整性
  ikos-cache verify --model damo/nlp_csanmt_translationzh2en
        """
    )
    
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="自定义缓存目录"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示缓存统计")
    stats_parser.set_defaults(func=cmd_stats)
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有模型")
    list_parser.set_defaults(func=cmd_list)
    
    # clean 命令
    clean_parser = subparsers.add_parser("clean", help="清理缓存")
    clean_parser.add_argument("--model", help="指定模型 ID")
    clean_parser.add_argument("--days", type=int, help="清理 N 天前的模型")
    clean_parser.add_argument("--all", action="store_true", help="清理所有缓存")
    clean_parser.set_defaults(func=cmd_clean)
    
    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="验证模型完整性")
    verify_parser.add_argument("--model", required=True, help="模型 ID")
    verify_parser.add_argument("--revision", default="master", help="版本分支")
    verify_parser.set_defaults(func=cmd_verify)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
