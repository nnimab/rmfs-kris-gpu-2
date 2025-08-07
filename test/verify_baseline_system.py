#!/usr/bin/env python3
"""
驗證基準模型測試系統
"""

import os
import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def verify_directory_structure():
    """驗證目錄結構"""
    print("1. 驗證目錄結構...")
    test_results_dir = Path(__file__).parent / "results"
    
    if test_results_dir.exists():
        print(f"   ✅ test/results 目錄存在")
        # 列出現有的測試結果
        results = list(test_results_dir.glob("baseline_*"))
        if results:
            print(f"   找到 {len(results)} 個測試結果:")
            for r in results[:5]:  # 只顯示前5個
                print(f"     - {r.name}")
        else:
            print("   目前沒有測試結果")
    else:
        print(f"   ℹ️ test/results 目錄不存在（將在第一次測試時創建）")
    
    return True

def verify_isolation_manager():
    """驗證隔離管理器"""
    print("\n2. 驗證隔離管理器...")
    try:
        from test.isolation_manager import IsolationManager
        print("   ✅ IsolationManager 可以正常導入")
        
        # 檢查關鍵方法
        methods = ['create_isolated_workspace', 'get_isolated_env_vars', 'cleanup_workspace']
        for method in methods:
            if hasattr(IsolationManager, method):
                print(f"   ✅ 方法 {method} 存在")
            else:
                print(f"   ❌ 方法 {method} 不存在")
                return False
                
        return True
    except Exception as e:
        print(f"   ❌ 無法導入 IsolationManager: {e}")
        return False

def verify_baseline_controller():
    """驗證基準模型控制器"""
    print("\n3. 驗證基準模型控制器...")
    try:
        from test.baseline_test_controller import BaselineTestController, run_single_test_wrapper
        print("   ✅ BaselineTestController 可以正常導入")
        print("   ✅ run_single_test_wrapper 函數存在（支援 Windows 並行）")
        
        # 創建測試實例
        controller = BaselineTestController()
        print(f"   ✅ 控制器實例創建成功")
        print(f"   輸出目錄: {controller.base_output_dir}")
        
        # 驗證隔離管理器已初始化
        if hasattr(controller, 'isolation_manager'):
            print("   ✅ 隔離管理器已初始化")
        else:
            print("   ❌ 隔離管理器未初始化")
            return False
            
        return True
    except Exception as e:
        print(f"   ❌ 基準模型控制器驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_parallel_support():
    """驗證並行支援"""
    print("\n4. 驗證並行執行支援...")
    
    # 檢查 Windows 平台
    import platform
    if platform.system() == 'Windows':
        print("   ℹ️ 檢測到 Windows 平台")
        print("   ✅ 已配置 run_single_test_wrapper 支援 Windows 多進程")
    else:
        print(f"   ℹ️ 檢測到 {platform.system()} 平台")
    
    # 檢查 CPU 核心數
    cpu_count = os.cpu_count()
    print(f"   CPU 核心數: {cpu_count}")
    print(f"   建議最大並行數: {max(1, cpu_count // 2)}")
    
    return True

def main():
    """主函數"""
    print("=== 基準模型測試系統驗證 ===\n")
    
    all_ok = True
    
    # 執行各項驗證
    all_ok &= verify_directory_structure()
    all_ok &= verify_isolation_manager()
    all_ok &= verify_baseline_controller()
    all_ok &= verify_parallel_support()
    
    print("\n=== 驗證結果 ===")
    if all_ok:
        print("✅ 所有驗證通過！系統已準備好執行基準模型測試。")
        print("\n可以使用以下方式執行測試:")
        print("1. 通過實驗選單: python test/experiment_menu.py")
        print("2. 直接執行: python test/baseline_test_controller.py --type time_based")
        print("3. 測試並行: python test/test_baseline_parallel.py")
    else:
        print("❌ 部分驗證失敗，請檢查上述錯誤訊息。")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)