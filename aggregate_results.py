#!/usr/bin/env python3
"""
多會話評估結果聚合工具
用於合併多個獨立評估會話的結果並生成比較圖表
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import argparse

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ResultAggregator:
    def __init__(self, evaluation_dirs, output_dir=None):
        """
        初始化結果聚合器
        
        Args:
            evaluation_dirs: 評估目錄列表
            output_dir: 輸出目錄（如果為 None，則使用第一個評估目錄）
        """
        self.evaluation_dirs = [Path(d) for d in evaluation_dirs]
        self.output_dir = Path(output_dir) if output_dir else self.evaluation_dirs[0]
        self.aggregated_results = {}
        
    def load_all_results(self):
        """載入所有評估結果"""
        print(f"正在載入 {len(self.evaluation_dirs)} 個評估結果...")
        
        for eval_dir in self.evaluation_dirs:
            if not eval_dir.exists():
                print(f"警告：目錄不存在 - {eval_dir}")
                continue
                
            # 尋找 JSON 結果文件
            json_files = list(eval_dir.glob("evaluation_results_*.json"))
            if not json_files:
                print(f"警告：未找到結果文件 - {eval_dir}")
                continue
                
            # 載入最新的結果文件
            latest_json = max(json_files, key=os.path.getctime)
            
            try:
                with open(latest_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 提取結果
                results = data.get('results', {})
                for controller_name, controller_data in results.items():
                    if controller_name not in self.aggregated_results:
                        self.aggregated_results[controller_name] = controller_data
                        print(f"✓ 載入 {controller_name} 的結果")
                    else:
                        print(f"⚠ 跳過重複的 {controller_name}")
                        
            except Exception as e:
                print(f"錯誤：無法載入 {latest_json} - {e}")
                
        print(f"\n成功載入 {len(self.aggregated_results)} 個控制器的結果")
        
    def generate_comparison_charts(self):
        """生成比較圖表（與 evaluate.py 相同的邏輯）"""
        if not self.aggregated_results:
            print("錯誤：沒有可用的結果進行比較")
            return
            
        # 準備數據
        controllers = []
        completion_rates = []
        avg_wait_times = []
        energy_per_orders = []
        robot_utilizations = []
        
        for name, data in self.aggregated_results.items():
            avg_perf = data['average_performance']
            controllers.append(name)
            completion_rates.append(avg_perf['completion_rate'] * 100)
            avg_wait_times.append(avg_perf['avg_wait_time'])
            energy_per_orders.append(avg_perf['energy_per_order'])
            robot_utilizations.append(avg_perf['robot_utilization'] * 100)
        
        # 創建比較圖表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('控制器性能評估比較（多會話聚合）', fontsize=16, fontweight='bold')
        
        # 設置顏色
        colors = plt.cm.Set3(np.linspace(0, 1, len(controllers)))
        
        # 完成率比較
        bars1 = axes[0,0].bar(controllers, completion_rates, color=colors)
        axes[0,0].set_title('訂單完成率比較', fontweight='bold')
        axes[0,0].set_ylabel('完成率 (%)')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 添加數值標籤
        for bar, rate in zip(bars1, completion_rates):
            height = bar.get_height()
            axes[0,0].text(bar.get_x() + bar.get_width()/2., height + 0.5,
                          f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 平均等待時間比較
        bars2 = axes[0,1].bar(controllers, avg_wait_times, color=colors)
        axes[0,1].set_title('平均等待時間比較', fontweight='bold')
        axes[0,1].set_ylabel('等待時間 (ticks)')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        for bar, wait in zip(bars2, avg_wait_times):
            height = bar.get_height()
            axes[0,1].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                          f'{wait:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 能源效率比較
        bars3 = axes[1,0].bar(controllers, energy_per_orders, color=colors)
        axes[1,0].set_title('能源效率比較', fontweight='bold')
        axes[1,0].set_ylabel('每訂單能源消耗')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        for bar, energy in zip(bars3, energy_per_orders):
            height = bar.get_height()
            if height > 0:
                axes[1,0].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                              f'{energy:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 機器人利用率比較
        bars4 = axes[1,1].bar(controllers, robot_utilizations, color=colors)
        axes[1,1].set_title('機器人利用率比較', fontweight='bold')
        axes[1,1].set_ylabel('利用率 (%)')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        for bar, util in zip(bars4, robot_utilizations):
            height = bar.get_height()
            axes[1,1].text(bar.get_x() + bar.get_width()/2., height + 1,
                          f'{util:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # 保存圖表
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        chart_file = self.output_dir / f"aggregated_comparison_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✓ 比較圖表已保存: {chart_file}")
        
    def generate_aggregated_report(self):
        """生成聚合報告"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_file = self.output_dir / f"aggregated_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RMFS 多會話評估聚合報告\n")
            f.write("="*60 + "\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"聚合來源: {len(self.evaluation_dirs)} 個評估目錄\n\n")
            
            # 列出所有來源目錄
            f.write("評估目錄列表:\n")
            for i, dir_path in enumerate(self.evaluation_dirs, 1):
                f.write(f"{i}. {dir_path}\n")
            f.write("\n")
            
            if self.aggregated_results:
                # 按完成率排序
                sorted_by_completion = sorted(
                    self.aggregated_results.items(),
                    key=lambda x: x[1]['average_performance']['completion_rate'],
                    reverse=True
                )
                
                f.write("控制器性能排名（按完成率）:\n")
                f.write("-" * 40 + "\n")
                for i, (name, data) in enumerate(sorted_by_completion, 1):
                    avg_perf = data['average_performance']
                    f.write(f"{i}. {name}: {avg_perf['completion_rate']*100:.1f}% "
                           f"(±{avg_perf['completion_rate_std']*100:.1f}%)\n")
                
                # 詳細性能
                f.write("\n詳細性能數據:\n")
                f.write("-" * 40 + "\n")
                for name, data in self.aggregated_results.items():
                    avg_perf = data['average_performance']
                    f.write(f"\n{name}:\n")
                    f.write(f"  完成率: {avg_perf['completion_rate']*100:.1f}%\n")
                    f.write(f"  平均等待時間: {avg_perf['avg_wait_time']:.1f} ticks\n")
                    f.write(f"  機器人利用率: {avg_perf['robot_utilization']*100:.1f}%\n")
                    if avg_perf.get('energy_per_order', 0) > 0:
                        f.write(f"  每訂單能源消耗: {avg_perf['energy_per_order']:.0f}\n")
        
        print(f"✓ 聚合報告已保存: {report_file}")
        
    def save_aggregated_json(self):
        """保存聚合的 JSON 結果"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        json_file = self.output_dir / f"aggregated_results_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'aggregation_time': timestamp,
                'source_directories': [str(d) for d in self.evaluation_dirs],
                'results': self.aggregated_results
            }, f, indent=2, ensure_ascii=False)
            
        print(f"✓ 聚合結果已保存: {json_file}")
        
def main():
    parser = argparse.ArgumentParser(description="聚合多個評估會話的結果")
    parser.add_argument('directories', nargs='+', 
                       help='評估目錄列表（空格分隔）')
    parser.add_argument('--output', '-o', 
                       help='輸出目錄（預設使用第一個評估目錄）')
    
    args = parser.parse_args()
    
    # 創建聚合器
    aggregator = ResultAggregator(args.directories, args.output)
    
    # 執行聚合
    print("開始聚合評估結果...\n")
    aggregator.load_all_results()
    
    if aggregator.aggregated_results:
        aggregator.generate_comparison_charts()
        aggregator.generate_aggregated_report()
        aggregator.save_aggregated_json()
        print("\n✅ 聚合完成！")
    else:
        print("\n❌ 沒有找到可用的評估結果")

if __name__ == "__main__":
    main()