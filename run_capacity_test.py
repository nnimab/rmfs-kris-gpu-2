#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMFS 容量測試系統主入口

提供容量測試系統的統一入口，支援命令列和互動式選單兩種模式。
"""

import sys
import argparse
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='RMFS 容量測試系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  
  # 互動式選單模式（推薦）
  python run_capacity_test.py
  
  # 直接執行容量測試
  python run_capacity_test.py --test --robot-counts 20 25 30 --ticks 50000
  
  # 生成分析報告
  python run_capacity_test.py --analyze test/results/capacity_test_20240101_120000
  
  # 執行基本功能測試
  python run_capacity_test.py --test-basic
  
  # 清理臨時檔案
  python run_capacity_test.py --cleanup
        """
    )
    
    # 模式選擇
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--menu', action='store_true', default=True,
                           help='啟動互動式選單（預設模式）')
    mode_group.add_argument('--test', action='store_true',
                           help='直接執行容量測試')
    mode_group.add_argument('--analyze', metavar='RESULTS_DIR',
                           help='分析指定目錄的測試結果')
    mode_group.add_argument('--test-basic', action='store_true',
                           help='執行基本功能測試')
    mode_group.add_argument('--cleanup', action='store_true',
                           help='清理所有臨時檔案')
    
    # 測試參數
    test_group = parser.add_argument_group('測試參數')
    test_group.add_argument('--robot-counts', nargs='+', type=int, default=[20, 25, 30, 35, 40],
                           help='要測試的機器人數量列表 (預設: 20 25 30 35 40)')
    test_group.add_argument('--ticks', type=int, default=100000,
                           help='每個測試的 tick 數 (預設: 100000)')
    test_group.add_argument('--parallel', action='store_true', default=True,
                           help='是否並行執行測試 (預設: True)')
    test_group.add_argument('--max-parallel', type=int, default=None,
                           help='最大並行測試數量 (預設: 自動)')
    test_group.add_argument('--output-dir', type=str, default=None,
                           help='輸出目錄路徑 (預設: 自動生成)')
    
    args = parser.parse_args()
    
    # 如果沒有指定任何模式，或明確指定 --menu，則進入選單模式
    if args.menu or not any([args.test, args.analyze, args.test_basic, args.cleanup]):
        run_interactive_menu()
    elif args.test:
        run_capacity_test(args)
    elif args.analyze:
        run_analysis(args.analyze)
    elif args.test_basic:
        run_basic_test()
    elif args.cleanup:
        run_cleanup()


def run_interactive_menu():
    """執行互動式選單"""
    try:
        from test.experiment_menu import ExperimentMenu
        
        print("🤖 正在啟動 RMFS 容量測試互動式選單...")
        menu = ExperimentMenu()
        menu.run()
        
    except ImportError:
        print("❌ 找不到互動式選單模組，請確保 rich 庫已安裝：pip install rich")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 互動式選單執行時發生錯誤: {e}")
        sys.exit(1)


def run_capacity_test(args):
    """直接執行容量測試"""
    try:
        from test.capacity_test_controller import CapacityTestController
        
        print("🚀 正在啟動容量測試...")
        print(f"📊 機器人數量: {args.robot_counts}")
        print(f"⏱️  測試時長: {args.ticks:,} ticks")
        print(f"⚡ 並行執行: {'是' if args.parallel else '否'}")
        
        # 創建測試控制器
        controller = CapacityTestController(args.output_dir)
        
        # 執行測試
        summary = controller.run_capacity_test(
            robot_counts=args.robot_counts,
            parallel=args.parallel,
            test_ticks=args.ticks,
            max_parallel_tests=args.max_parallel
        )
        
        # 顯示結果
        print(f"\n✅ 容量測試完成")
        print(f"成功測試: {summary['completed_tests']}/{summary['total_tests']}")
        print(f"總執行時間: {summary['total_execution_time']:.1f} 秒")
        print(f"結果目錄: {controller.base_output_dir}")
        
        # 自動生成分析報告
        try:
            report_path = controller.generate_capacity_analysis()
            if report_path:
                print(f"分析報告: {report_path}")
        except Exception as e:
            print(f"⚠️  生成分析報告時發生錯誤: {e}")
        
    except KeyboardInterrupt:
        print("\n❌ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 容量測試執行時發生錯誤: {e}")
        sys.exit(1)


def run_analysis(results_dir):
    """執行結果分析"""
    try:
        from test.capacity_analyzer import CapacityAnalyzer
        
        print(f"📈 正在分析測試結果: {results_dir}")
        
        analyzer = CapacityAnalyzer(Path(results_dir))
        report_path = analyzer.generate_analysis_report()
        
        if report_path:
            print(f"✅ 分析報告已生成: {report_path}")
        else:
            print("❌ 分析報告生成失敗")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ 結果分析時發生錯誤: {e}")
        sys.exit(1)


def run_basic_test():
    """執行基本功能測試"""
    try:
        from test.test_basic_functionality import BasicFunctionalityTest
        
        print("🧪 正在執行基本功能測試...")
        
        test_runner = BasicFunctionalityTest()
        results = test_runner.run_all_tests()
        
        # 檢查是否所有測試都通過
        all_passed = all(results.values())
        if not all_passed:
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ 基本功能測試時發生錯誤: {e}")
        sys.exit(1)


def run_cleanup():
    """執行清理操作"""
    try:
        import shutil
        from pathlib import Path
        
        print("🧹 正在清理臨時檔案...")
        
        # 清理可能的臨時目錄和檔案
        cleanup_paths = [
            Path("test/results"),
            Path("states"),
            Path("*.tmp"),
            Path("temp_*")
        ]
        
        cleaned_count = 0
        
        for path_pattern in cleanup_paths:
            if path_pattern.is_dir():
                try:
                    shutil.rmtree(path_pattern)
                    cleaned_count += 1
                    print(f"✅ 已清理目錄: {path_pattern}")
                except Exception as e:
                    print(f"⚠️  清理 {path_pattern} 時發生錯誤: {e}")
            elif '*' in str(path_pattern):
                # 處理萬用字元模式
                import glob
                for file_path in glob.glob(str(path_pattern)):
                    try:
                        Path(file_path).unlink()
                        cleaned_count += 1
                        print(f"✅ 已清理檔案: {file_path}")
                    except Exception as e:
                        print(f"⚠️  清理 {file_path} 時發生錯誤: {e}")
        
        print(f"🎉 清理完成，共清理 {cleaned_count} 個項目")
        
    except Exception as e:
        print(f"❌ 清理操作時發生錯誤: {e}")
        sys.exit(1)


def check_dependencies():
    """檢查依賴項"""
    required_modules = [
        ('pandas', 'pip install pandas'),
        ('numpy', 'pip install numpy'),
        ('matplotlib', 'pip install matplotlib'),
        ('rich', 'pip install rich')
    ]
    
    missing_modules = []
    
    for module_name, install_cmd in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append((module_name, install_cmd))
    
    if missing_modules:
        print("❌ 缺少必要的依賴項:")
        for module_name, install_cmd in missing_modules:
            print(f"  - {module_name}: {install_cmd}")
        return False
    
    return True


if __name__ == '__main__':
    # 檢查依賴項
    if not check_dependencies():
        print("\n請安裝缺少的依賴項後再次執行。")
        sys.exit(1)
    
    # 執行主程式
    main()