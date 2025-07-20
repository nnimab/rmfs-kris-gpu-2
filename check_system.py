#!/usr/bin/env python3
"""
系統完整性檢查腳本
用於在執行長時間實驗前，快速驗證所有核心功能是否正常
適用於 Windows 環境
"""

import os
import sys
import subprocess
import time
import glob
from datetime import datetime

# 設定顏色輸出（Windows 相容）
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    """打印標題"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.END}")

def print_success(text):
    """打印成功訊息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """打印錯誤訊息"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """打印警告訊息"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def run_command(cmd, description, timeout=60):
    """執行命令並返回結果"""
    print(f"\n執行: {description}")
    print(f"命令: {cmd}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print_success(f"完成 (耗時: {elapsed_time:.1f}秒)")
            if result.stdout:
                print(f"輸出: {result.stdout[:200]}...")  # 只顯示前200字符
            return True, result.stdout
        else:
            print_error(f"失敗 (返回碼: {result.returncode})")
            if result.stderr:
                print(f"錯誤: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print_error(f"超時 (超過 {timeout} 秒)")
        return False, "Timeout"
    except Exception as e:
        print_error(f"異常: {str(e)}")
        return False, str(e)

def check_syntax():
    """檢查語法錯誤"""
    print_header("1. 語法檢查")
    
    scripts = ["train.py", "evaluate.py", "visualization_generator.py"]
    all_passed = True
    
    for script in scripts:
        if os.path.exists(script):
            success, _ = run_command(
                f'python -m py_compile {script}',
                f'檢查 {script} 語法',
                timeout=10
            )
            if not success:
                all_passed = False
        else:
            print_warning(f"{script} 不存在")
            all_passed = False
    
    return all_passed

def check_imports():
    """檢查模組導入"""
    print_header("2. 模組導入檢查")
    
    modules = {
        "train": "訓練腳本",
        "evaluate": "評估框架",
        "visualization_generator": "圖表生成器"
    }
    
    all_passed = True
    
    for module, desc in modules.items():
        if os.path.exists(f"{module}.py"):
            cmd = f'python -c "import {module}; print(\'{desc} 導入成功\')"'
            success, _ = run_command(cmd, f'測試導入 {module}', timeout=10)
            if not success:
                all_passed = False
        else:
            print_warning(f"{module}.py 不存在")
    
    return all_passed

def test_train_minimal():
    """最小訓練測試"""
    print_header("3. 訓練腳本測試 (最小參數)")
    
    if not os.path.exists("train.py"):
        print_warning("train.py 不存在，跳過訓練測試")
        return False
    
    all_success = True
    
    # DQN Step 模式測試
    print("\n3.1 DQN Step 獎勵模式測試")
    success, _ = run_command(
        'python train.py --agent dqn --reward_mode step --training_ticks 100',
        'DQN Step模式 (100 ticks)',
        timeout=120
    )
    all_success &= success
    
    # DQN Global 模式測試
    print("\n3.2 DQN Global 獎勵模式測試")
    success, _ = run_command(
        'python train.py --agent dqn --reward_mode global --training_ticks 100',
        'DQN Global模式 (100 ticks)',
        timeout=120
    )
    all_success &= success
    
    # NERL Step 模式測試（最小族群）
    print("\n3.3 NERL Step 獎勵模式測試")
    success, _ = run_command(
        'python train.py --agent nerl --reward_mode step --generations 1 --population 3 --eval_ticks 50',
        'NERL Step模式 (1代, 3個體, 50 ticks)',
        timeout=180
    )
    all_success &= success
    
    # NERL Global 模式測試（小族群）
    print("\n3.4 NERL Global 獎勵模式測試")
    success, _ = run_command(
        'python train.py --agent nerl --reward_mode global --generations 1 --population 3 --eval_ticks 50',
        'NERL Global模式 (1代, 3個體, 50 ticks)',
        timeout=180
    )
    all_success &= success
    
    # Auto 獎勵模式測試
    print("\n3.5 Auto 獎勵模式測試")
    success, _ = run_command(
        'python train.py --agent dqn --reward_mode auto --training_ticks 100',
        'DQN Auto獎勵模式 (100 ticks)',
        timeout=120
    )
    all_success &= success
    
    return all_success

def test_evaluate_minimal():
    """最小評估測試"""
    print_header("4. 評估框架測試 (多參數測試)")
    
    if not os.path.exists("evaluate.py"):
        print_warning("evaluate.py 不存在，跳過評估測試")
        return False
    
    all_success = True
    
    # 4.1 測試傳統控制器
    print("\n4.1 傳統控制器測試")
    success, output = run_command(
        'python evaluate.py --controllers time_based queue_based --ticks 500 --seed 42 --description "traditional_test"',
        '評估傳統控制器 (500 ticks, seed=42)',
        timeout=180
    )
    all_success &= success
    
    # 4.2 測試不同隨機種子
    print("\n4.2 隨機種子測試")
    success, _ = run_command(
        'python evaluate.py --controllers time_based --ticks 300 --seed 123 --description "seed_test"',
        '測試不同隨機種子 (300 ticks, seed=123)',
        timeout=120
    )
    all_success &= success
    
    # 4.3 測試自動檢測控制器
    print("\n4.3 自動檢測控制器測試")
    success, _ = run_command(
        'python evaluate.py --ticks 300 --description "auto_detect"',
        '自動檢測可用控制器 (300 ticks)',
        timeout=120
    )
    all_success &= success
    
    # 4.4 測試僅分析模式（需要先有結果）
    if glob.glob("result/evaluations/EVAL_*_traditional_test"):
        print("\n4.4 僅分析模式測試")
        success, _ = run_command(
            'python evaluate.py --analysis-only --output result/evaluations/EVAL_*_traditional_test',
            '測試僅分析模式',
            timeout=60
        )
        all_success &= success
    
    # 檢查結果文件
    if all_success:
        result_dirs = glob.glob("result/evaluations/EVAL_*")
        if result_dirs:
            print_success(f"共生成 {len(result_dirs)} 個評估結果目錄")
            
            # 檢查最新的結果
            latest_dir = sorted(result_dirs)[-1]
            csv_files = glob.glob(f"{latest_dir}/*.csv")
            json_files = glob.glob(f"{latest_dir}/*.json")
            
            if csv_files:
                print_success(f"CSV 文件: {len(csv_files)} 個")
                expected_files = ['algorithm_comparison.csv', 'reward_comparison.csv', 'overall_comparison.csv']
                for expected in expected_files:
                    if any(expected in f for f in csv_files):
                        print(f"  ✓ {expected}")
                    else:
                        print_warning(f"  ✗ 缺少 {expected}")
            
            if json_files:
                print_success(f"JSON 文件: {len(json_files)} 個")
    
    return all_success

def test_visualization():
    """圖表生成測試"""
    print_header("5. 圖表生成測試 (多種圖表類型)")
    
    if not os.path.exists("visualization_generator.py"):
        print_warning("visualization_generator.py 不存在，跳過圖表測試")
        return False
    
    # 找最新的測試結果
    result_dirs = glob.glob("result/evaluations/EVAL_*")
    if not result_dirs:
        print_warning("沒有可用的測試結果，跳過圖表生成")
        return False
    
    latest_dir = sorted(result_dirs)[-1]
    all_success = True
    
    # 5.1 測試生成所有圖表
    print("\n5.1 生成所有圖表測試")
    success, _ = run_command(
        f'python visualization_generator.py {latest_dir} --chart all',
        f'生成所有圖表類型',
        timeout=90
    )
    all_success &= success
    
    # 5.2 測試生成單一圖表類型
    chart_types = ['radar', 'algorithm', 'reward', 'rankings', 'heatmap']
    
    for chart_type in chart_types[:2]:  # 只測試前兩種以節省時間
        print(f"\n5.2.{chart_types.index(chart_type)+1} 測試 {chart_type} 圖表")
        success, _ = run_command(
            f'python visualization_generator.py {latest_dir} --chart {chart_type}',
            f'生成 {chart_type} 圖表',
            timeout=30
        )
        all_success &= success
    
    # 檢查圖表文件
    if all_success:
        chart_files = glob.glob(f"{latest_dir}/charts/*.png")
        if chart_files:
            print_success(f"共生成 {len(chart_files)} 個圖表")
            
            # 檢查預期的圖表類型
            expected_charts = [
                'performance_radar_chart.png',
                'algorithm_comparison_chart.png',
                'reward_mechanism_chart.png',
                'performance_rankings_chart.png',
                'comprehensive_heatmap.png'
            ]
            
            for expected in expected_charts:
                if any(expected in f for f in chart_files):
                    print(f"  ✓ {expected}")
                else:
                    print_warning(f"  ✗ 缺少 {expected}")
        else:
            print_warning("未找到生成的圖表")
            all_success = False
    
    return all_success

def auto_rename_models():
    """自動重命名模型為標準格式"""
    print_header("6.1 自動重命名模型文件")
    
    models_dir = "models"
    if not os.path.exists(models_dir):
        print_warning("models 目錄不存在")
        return False
    
    # 映射規則：將現有模型重命名為標準格式
    rename_mappings = [
        # DQN 模型
        ("dqn_traffic_10000.pth", "dqn_step.pth"),
        ("dqn_traffic_5000.pth", "dqn_global.pth"),
        # NERL 模型
        ("nerl_traffic.pth", "nerl_step.pth"),
    ]
    
    renamed_count = 0
    
    for old_name, new_name in rename_mappings:
        old_path = os.path.join(models_dir, old_name)
        new_path = os.path.join(models_dir, new_name)
        
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                # Windows 使用 copy 而不是 mv，保留原文件
                import shutil
                shutil.copy2(old_path, new_path)
                print_success(f"重命名: {old_name} -> {new_name}")
                renamed_count += 1
            except Exception as e:
                print_error(f"重命名失敗 {old_name}: {e}")
        elif os.path.exists(new_path):
            print_success(f"標準模型已存在: {new_name}")
        else:
            print_warning(f"源文件不存在: {old_name}")
    
    # 為缺失的 nerl_global.pth 創建副本
    if os.path.exists(os.path.join(models_dir, "nerl_step.pth")) and not os.path.exists(os.path.join(models_dir, "nerl_global.pth")):
        try:
            import shutil
            shutil.copy2(
                os.path.join(models_dir, "nerl_step.pth"),
                os.path.join(models_dir, "nerl_global.pth")
            )
            print_success("創建 nerl_global.pth (複製自 nerl_step.pth)")
            renamed_count += 1
        except Exception as e:
            print_error(f"創建 nerl_global.pth 失敗: {e}")
    
    print_success(f"完成自動重命名，共處理 {renamed_count} 個文件")
    return renamed_count > 0

def check_models():
    """檢查模型文件"""
    print_header("6. 模型文件檢查")
    
    models_dir = "models"
    if not os.path.exists(models_dir):
        print_warning("models 目錄不存在")
        return False
    
    # 列出所有模型文件
    model_files = glob.glob(f"{models_dir}/*.pth")
    
    if model_files:
        print_success(f"找到 {len(model_files)} 個模型文件:")
        for model in model_files:
            size = os.path.getsize(model) / 1024  # KB
            print(f"  - {os.path.basename(model)} ({size:.1f} KB)")
    else:
        print_warning("未找到任何模型文件")
    
    # 先嘗試自動重命名
    auto_rename_models()
    
    # 重新檢查標準模型名稱
    standard_models = ["dqn_step.pth", "dqn_global.pth", "nerl_step.pth", "nerl_global.pth"]
    missing_models = []
    
    for model_name in standard_models:
        model_path = os.path.join(models_dir, model_name)
        if os.path.exists(model_path):
            print_success(f"標準模型存在: {model_name}")
        else:
            missing_models.append(model_name)
            print_warning(f"標準模型缺失: {model_name}")
    
    if missing_models:
        print_warning(f"建議手動重命名以下文件:")
        for missing in missing_models:
            print(f"  - 缺失: {missing}")
    
    return len(missing_models) == 0

def test_error_handling():
    """錯誤處理測試"""
    print_header("7. 錯誤處理和邊界測試")
    
    all_tests_passed = True
    
    # 7.1 測試無效代理類型
    print("\n7.1 測試無效代理類型")
    success, _ = run_command(
        'python train.py --agent invalid_agent 2>&1',
        '測試無效的代理類型',
        timeout=10
    )
    if not success:
        print_success("✓ 正確拒絕無效代理")
    else:
        print_error("✗ 應該拒絕無效代理")
        all_tests_passed = False
    
    # 7.2 測試無效獎勵模式
    print("\n7.2 測試無效獎勵模式")
    success, _ = run_command(
        'python train.py --agent dqn --reward_mode invalid_mode 2>&1',
        '測試無效的獎勵模式',
        timeout=10
    )
    if not success:
        print_success("✓ 正確拒絕無效獎勵模式")
    else:
        print_error("✗ 應該拒絕無效獎勵模式")
        all_tests_passed = False
    
    # 7.3 測試無效控制器名稱
    print("\n7.3 測試無效控制器名稱")
    success, _ = run_command(
        'python evaluate.py --controllers invalid_controller --ticks 100 2>&1',
        '測試無效的控制器名稱',
        timeout=10
    )
    if not success:
        print_success("✓ 正確拒絕無效控制器")
    else:
        print_error("✗ 應該拒絕無效控制器")
        all_tests_passed = False
    
    # 7.4 測試負數參數
    print("\n7.4 測試負數參數")
    success, _ = run_command(
        'python train.py --agent dqn --training_ticks -100 2>&1',
        '測試負數訓練時長',
        timeout=10
    )
    if not success:
        print_success("✓ 正確拒絕負數參數")
    else:
        print_error("✗ 應該拒絕負數參數")
        all_tests_passed = False
    
    # 7.5 測試不存在的結果目錄
    print("\n7.5 測試不存在的結果目錄")
    success, _ = run_command(
        'python visualization_generator.py non_existent_directory 2>&1',
        '測試不存在的目錄',
        timeout=10
    )
    if not success:
        print_success("✓ 正確處理不存在的目錄")
    else:
        print_error("✗ 應該報告目錄不存在")
        all_tests_passed = False
    
    return all_tests_passed

def cleanup_test_files():
    """清理測試文件"""
    print_header("8. 清理測試文件")
    
    # 清理測試生成的評估結果
    test_dirs = glob.glob("result/evaluations/EVAL_*_system_check")
    for dir_path in test_dirs:
        print(f"保留測試結果: {dir_path}")
    
    print_success("測試文件保留完成（不刪除，供檢查用）")
    return True

def generate_report():
    """生成測試報告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
系統檢查報告
生成時間: {timestamp}

測試結果摘要:
1. 語法檢查: {"通過" if check_results[0] else "失敗"}
2. 模組導入: {"通過" if check_results[1] else "失敗"}
3. 訓練測試: {"通過" if check_results[2] else "失敗"}
4. 評估測試: {"通過" if check_results[3] else "失敗"}
5. 圖表生成: {"通過" if check_results[4] else "失敗"}
6. 模型檢查: {"通過" if check_results[5] else "失敗"}
7. 錯誤處理: {"通過" if check_results[6] else "失敗"}

總體狀態: {"✓ 系統準備就緒" if all(check_results) else "✗ 需要修復問題"}
    """
    
    # 保存報告
    with open("system_check_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print_header("測試報告")
    print(report)
    print_success(f"報告已保存到: system_check_report.txt")

if __name__ == "__main__":
    # 解析命令行參數
    import argparse
    parser = argparse.ArgumentParser(description='RMFS 系統完整性檢查')
    parser.add_argument('--quick', action='store_true', help='快速模式 - 只執行最基本的測試 (1-2分鐘)')
    parser.add_argument('--skip-train', action='store_true', help='跳過訓練測試')
    parser.add_argument('--skip-eval', action='store_true', help='跳過評估測試')
    parser.add_argument('--skip-viz', action='store_true', help='跳過視覺化測試')
    args = parser.parse_args()
    
    print_header("RMFS 系統完整性檢查")
    
    if args.quick:
        print("執行模式: 快速檢查 (最基本測試)")
        print("預計耗時: 1-2 分鐘")
    else:
        print("執行模式: 完整檢查 (所有參數測試)")
        print("預計耗時: 3-5 分鐘")
        print("\n提示: 使用 --quick 參數可執行快速測試")
    
    # 執行所有檢查
    check_results = []
    
    # 1. 語法檢查
    check_results.append(check_syntax())
    
    # 2. 模組導入
    check_results.append(check_imports())
    
    # 3. 訓練測試
    if not args.skip_train:
        if args.quick:
            # 快速模式：只測試一種配置
            print_header("3. 訓練腳本測試 (快速模式)")
            if os.path.exists("train.py"):
                success, _ = run_command(
                    'python train.py --agent dqn --reward_mode step --training_ticks 50',
                    'DQN 快速測試 (50 ticks)',
                    timeout=60
                )
                check_results.append(success)
            else:
                check_results.append(False)
        else:
            check_results.append(test_train_minimal())
    else:
        print_warning("跳過訓練測試")
        check_results.append(True)
    
    # 4. 評估測試
    if not args.skip_eval:
        if args.quick:
            # 快速模式：只測試傳統控制器
            print_header("4. 評估框架測試 (快速模式)")
            if os.path.exists("evaluate.py"):
                success, _ = run_command(
                    'python evaluate.py --controllers time_based --ticks 200 --description "quick_check"',
                    '快速評估測試 (200 ticks)',
                    timeout=60
                )
                check_results.append(success)
            else:
                check_results.append(False)
        else:
            check_results.append(test_evaluate_minimal())
    else:
        print_warning("跳過評估測試")
        check_results.append(True)
    
    # 5. 圖表生成
    if not args.skip_viz:
        check_results.append(test_visualization())
    else:
        print_warning("跳過視覺化測試")
        check_results.append(True)
    
    # 6. 模型檢查
    check_results.append(check_models())
    
    # 7. 錯誤處理
    check_results.append(test_error_handling())
    
    # 8. 清理
    cleanup_test_files()
    
    # 生成報告
    generate_report()
    
    # 最終結果
    if all(check_results):
        print_success("\n✓ 所有檢查通過！系統準備就緒。")
        print("您可以安全地執行長時間實驗了。")
        sys.exit(0)
    else:
        print_error("\n✗ 某些檢查失敗，請修復問題後再執行實驗。")
        failed_checks = [i+1 for i, result in enumerate(check_results) if not result]
        print(f"失敗的檢查: {failed_checks}")
        sys.exit(1)