#!/usr/bin/env python3
"""
生成缺少的 capacity_test_summary.json 檔案
用於修復容量測試完成但未生成總結檔案的問題
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def collect_test_results(test_dir: Path) -> List[Dict[str, Any]]:
    """
    收集所有測試結果
    
    Args:
        test_dir: 測試目錄路徑
        
    Returns:
        測試結果列表
    """
    results = []
    workspaces_dir = test_dir / "workspaces"
    
    if not workspaces_dir.exists():
        print(f"錯誤：找不到 workspaces 目錄: {workspaces_dir}")
        return results
    
    # 遍歷所有工作空間目錄
    for workspace in sorted(workspaces_dir.iterdir()):
        if not workspace.is_dir():
            continue
            
        # 解析工作空間名稱
        # 格式: robots_20_run0_c8d8f1d2_robots_20
        parts = workspace.name.split('_')
        if len(parts) < 4:
            continue
            
        robot_count = int(parts[1])
        # run_index 在第3個位置，格式為 'run0'
        run_str = parts[2]
        if not run_str.startswith('run'):
            continue
        run_index = int(run_str.replace('run', ''))
        
        # 尋找評估結果
        result_path = workspace / "results"
        if not result_path.exists():
            continue
            
        # 找到結果子目錄
        for result_dir in result_path.iterdir():
            if not result_dir.is_dir():
                continue
                
            eval_json = result_dir / "evaluation_results.json"
            if eval_json.exists():
                try:
                    with open(eval_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # 建立測試結果記錄
                    result = {
                        'test_id': workspace.name,
                        'robot_count': robot_count,
                        'run_index': run_index,
                        'workspace_dir': str(workspace),
                        'status': 'completed',
                        'evaluation_results': data  # 改為 evaluation_results
                    }
                    
                    results.append(result)
                    print(f"收集結果: 機器人 {robot_count}, 第 {run_index} 次運行")
                    
                except Exception as e:
                    print(f"讀取結果失敗 {eval_json}: {e}")
                    
    return results


def generate_summary(test_dir: Path) -> Dict[str, Any]:
    """
    生成測試總結
    
    Args:
        test_dir: 測試目錄路徑
        
    Returns:
        測試總結
    """
    results = collect_test_results(test_dir)
    
    if not results:
        print("錯誤：沒有找到任何測試結果")
        return None
        
    # 統計資訊
    completed_count = len([r for r in results if r['status'] == 'completed'])
    failed_count = len([r for r in results if r['status'] == 'failed'])
    
    # 按機器人數量分組
    by_robot_count = {}
    for result in results:
        robot_count = result['robot_count']
        if robot_count not in by_robot_count:
            by_robot_count[robot_count] = []
        by_robot_count[robot_count].append(result)
    
    # 計算統計數據
    statistics = {}
    for robot_count, runs in sorted(by_robot_count.items()):
        stats = {
            'robot_count': robot_count,
            'runs': len(runs),
            'metrics': {}
        }
        
        # 收集所有運行的指標
        all_metrics = {}
        for run in runs:
            if 'result' in run and 'metrics' in run['result']:
                for metric, value in run['result']['metrics'].items():
                    if metric not in all_metrics:
                        all_metrics[metric] = []
                    all_metrics[metric].append(value)
        
        # 計算平均值
        for metric, values in all_metrics.items():
            if values:
                stats['metrics'][metric] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'values': values
                }
        
        statistics[robot_count] = stats
    
    # 建立總結
    summary = {
        'test_type': 'capacity_test',
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'completed': completed_count,
        'failed': failed_count,
        'test_configurations': sorted(list(by_robot_count.keys())),
        'runs_per_config': len(by_robot_count[list(by_robot_count.keys())[0]]) if by_robot_count else 0,
        'test_ticks': 10000,  # 從評估結果中取得的預設值
        'statistics': statistics,
        'all_results': results
    }
    
    return summary


def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("使用方法: python generate_missing_summary.py <測試目錄路徑>")
        print("例如: python generate_missing_summary.py test/results/capacity_test_20250805_225949_f61b24ad")
        return
        
    test_dir = Path(sys.argv[1])
    if not test_dir.exists():
        print(f"錯誤：測試目錄不存在: {test_dir}")
        return
        
    print(f"正在處理測試目錄: {test_dir}")
    
    # 生成總結
    summary = generate_summary(test_dir)
    if not summary:
        return
        
    # 儲存總結檔案
    summary_file = test_dir / "capacity_test_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\n成功生成總結檔案: {summary_file}")
    print(f"總測試數: {summary['total_tests']}")
    print(f"成功: {summary['completed']}")
    print(f"失敗: {summary['failed']}")
    print(f"測試配置: {summary['test_configurations']}")


if __name__ == "__main__":
    main()