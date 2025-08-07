#!/usr/bin/env python3
"""
基準模型分析器
用於分析 Time-Based 和 Queue-Based 控制器的參數掃描結果
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.logger import get_logger

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class BaselineAnalyzer:
    """基準模型分析器"""
    
    def __init__(self, session_dir: Path):
        """
        初始化分析器
        
        Args:
            session_dir: 測試會話目錄
        """
        self.session_dir = Path(session_dir)
        
        # 設置日誌
        log_file = self.session_dir / "baseline_analysis.log"
        self.logger = get_logger(log_file_path=str(log_file))
        
        # 創建分析結果目錄
        self.analysis_dir = self.session_dir / "analysis"
        self.analysis_dir.mkdir(exist_ok=True)
        
        # 載入測試摘要
        self.summary = self._load_summary()
        
    def _load_summary(self) -> Dict[str, Any]:
        """載入測試摘要"""
        summary_file = self.session_dir / 'baseline_test_summary.json'
        if not summary_file.exists():
            raise FileNotFoundError(f"找不到測試摘要檔案: {summary_file}")
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_all_results(self) -> pd.DataFrame:
        """載入所有測試結果並轉換為 DataFrame"""
        all_results = []
        
        for result in self.summary['results']:
            if result['status'] != 'completed':
                continue
                
            # 提取基本資訊
            test_record = {
                'test_id': result['test_id'],
                'robot_count': result['robot_count'],
                'run_index': result.get('run_index', 0),
            }
            
            # 根據測試類型提取參數
            if self.summary['test_type'] == 'time_based':
                test_record['parameter'] = result['time_ratio']
                test_record['parameter_type'] = 'time_ratio'
            else:  # queue_based
                test_record['parameter'] = str(result['queue_threshold'])
                test_record['parameter_type'] = 'queue_threshold'
            
            # 提取性能指標
            test_record['completion_rate'] = result.get('completion_rate', 0)
            test_record['avg_wait_time'] = result.get('avg_wait_time', 0)
            test_record['robot_utilization'] = result.get('robot_utilization', 0)
            test_record['total_energy'] = result.get('total_energy', 0)
            test_record['execution_time'] = result.get('execution_time', 0)
            
            all_results.append(test_record)
        
        return pd.DataFrame(all_results)
    
    def generate_parameter_comparison_chart(self) -> str:
        """生成參數比較圖表"""
        df = self._load_all_results()
        
        # 設置圖表大小和佈局
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f"{self.summary['test_type'].replace('_', ' ').title()} 參數掃描結果分析", 
                     fontsize=16, fontweight='bold')
        
        # 獲取唯一的機器人數量
        robot_counts = sorted(df['robot_count'].unique())
        
        # 定義顏色映射
        colors = plt.cm.Set1(np.linspace(0, 1, len(robot_counts)))
        
        # 1. 完成率 vs 參數
        ax1 = axes[0, 0]
        for i, robot_count in enumerate(robot_counts):
            subset = df[df['robot_count'] == robot_count]
            # 計算每個參數的平均值和標準差
            grouped = subset.groupby('parameter').agg({
                'completion_rate': ['mean', 'std']
            })
            
            x = grouped.index
            y = grouped['completion_rate']['mean']
            yerr = grouped['completion_rate']['std']
            
            ax1.errorbar(x, y, yerr=yerr, marker='o', label=f'{robot_count} 機器人',
                        color=colors[i], capsize=5, markersize=8)
        
        ax1.set_xlabel(self._get_parameter_label())
        ax1.set_ylabel('訂單完成率')
        ax1.set_title('訂單完成率 vs 參數設定')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1.1)
        
        # 2. 平均等待時間 vs 參數
        ax2 = axes[0, 1]
        for i, robot_count in enumerate(robot_counts):
            subset = df[df['robot_count'] == robot_count]
            grouped = subset.groupby('parameter').agg({
                'avg_wait_time': ['mean', 'std']
            })
            
            x = grouped.index
            y = grouped['avg_wait_time']['mean']
            yerr = grouped['avg_wait_time']['std']
            
            ax2.errorbar(x, y, yerr=yerr, marker='s', label=f'{robot_count} 機器人',
                        color=colors[i], capsize=5, markersize=8)
        
        ax2.set_xlabel(self._get_parameter_label())
        ax2.set_ylabel('平均等待時間 (ticks)')
        ax2.set_title('平均等待時間 vs 參數設定')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 機器人利用率 vs 參數
        ax3 = axes[1, 0]
        for i, robot_count in enumerate(robot_counts):
            subset = df[df['robot_count'] == robot_count]
            grouped = subset.groupby('parameter').agg({
                'robot_utilization': ['mean', 'std']
            })
            
            x = grouped.index
            y = grouped['robot_utilization']['mean']
            yerr = grouped['robot_utilization']['std']
            
            ax3.errorbar(x, y, yerr=yerr, marker='^', label=f'{robot_count} 機器人',
                        color=colors[i], capsize=5, markersize=8)
        
        ax3.set_xlabel(self._get_parameter_label())
        ax3.set_ylabel('機器人利用率')
        ax3.set_title('機器人利用率 vs 參數設定')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 1.1)
        
        # 4. 能源效率 vs 參數
        ax4 = axes[1, 1]
        for i, robot_count in enumerate(robot_counts):
            subset = df[df['robot_count'] == robot_count]
            # 計算每完成訂單的能源消耗
            subset['energy_per_order'] = subset.apply(
                lambda row: row['total_energy'] / (row['completion_rate'] * 1000) if row['completion_rate'] > 0 else np.nan,
                axis=1
            )
            
            grouped = subset.groupby('parameter').agg({
                'energy_per_order': ['mean', 'std']
            })
            
            # 過濾掉 NaN 值
            grouped = grouped.dropna()
            
            if len(grouped) > 0:
                x = grouped.index
                y = grouped['energy_per_order']['mean']
                yerr = grouped['energy_per_order']['std']
                
                ax4.errorbar(x, y, yerr=yerr, marker='D', label=f'{robot_count} 機器人',
                            color=colors[i], capsize=5, markersize=8)
        
        ax4.set_xlabel(self._get_parameter_label())
        ax4.set_ylabel('每訂單能源消耗')
        ax4.set_title('能源效率 vs 參數設定')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 調整佈局
        plt.tight_layout()
        
        # 保存圖表
        chart_path = self.analysis_dir / f"{self.summary['test_type']}_parameter_comparison.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"參數比較圖表已保存: {chart_path}")
        return str(chart_path)
    
    def generate_heatmap_analysis(self) -> str:
        """生成熱力圖分析"""
        df = self._load_all_results()
        
        # 創建樞紐表
        metrics = ['completion_rate', 'avg_wait_time', 'robot_utilization']
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f"{self.summary['test_type'].replace('_', ' ').title()} 參數熱力圖分析", 
                     fontsize=16, fontweight='bold')
        
        for idx, metric in enumerate(metrics):
            # 創建樞紐表（參數 x 機器人數量）
            pivot = df.pivot_table(
                values=metric,
                index='parameter',
                columns='robot_count',
                aggfunc='mean'
            )
            
            # 繪製熱力圖
            ax = axes[idx]
            
            # 選擇適當的顏色映射
            if metric == 'avg_wait_time':
                cmap = 'YlOrRd'  # 等待時間越低越好
            else:
                cmap = 'YlGn'  # 完成率和利用率越高越好
            
            sns.heatmap(pivot, annot=True, fmt='.3f', cmap=cmap, 
                       cbar_kws={'label': self._get_metric_label(metric)},
                       ax=ax)
            
            ax.set_title(self._get_metric_title(metric))
            ax.set_xlabel('機器人數量')
            ax.set_ylabel(self._get_parameter_label())
        
        plt.tight_layout()
        
        # 保存圖表
        chart_path = self.analysis_dir / f"{self.summary['test_type']}_heatmap_analysis.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"熱力圖分析已保存: {chart_path}")
        return str(chart_path)
    
    def generate_optimal_parameter_report(self) -> str:
        """生成最優參數報告"""
        df = self._load_all_results()
        
        # 計算每個參數組合的綜合分數
        # 分數 = 完成率 * 0.5 + 利用率 * 0.3 - 標準化等待時間 * 0.2
        df['wait_time_normalized'] = df['avg_wait_time'] / df['avg_wait_time'].max()
        df['composite_score'] = (
            df['completion_rate'] * 0.5 + 
            df['robot_utilization'] * 0.3 - 
            df['wait_time_normalized'] * 0.2
        )
        
        # 找出每個機器人數量的最優參數
        optimal_params = {}
        for robot_count in df['robot_count'].unique():
            subset = df[df['robot_count'] == robot_count]
            grouped = subset.groupby('parameter').agg({
                'composite_score': 'mean',
                'completion_rate': 'mean',
                'avg_wait_time': 'mean',
                'robot_utilization': 'mean'
            })
            
            # 找出最高分數的參數
            best_param = grouped['composite_score'].idxmax()
            best_metrics = grouped.loc[best_param]
            
            optimal_params[robot_count] = {
                'parameter': best_param,
                'composite_score': best_metrics['composite_score'],
                'completion_rate': best_metrics['completion_rate'],
                'avg_wait_time': best_metrics['avg_wait_time'],
                'robot_utilization': best_metrics['robot_utilization']
            }
        
        # 生成報告
        report_lines = [
            f"# {self.summary['test_type'].replace('_', ' ').title()} 最優參數分析報告",
            f"\n生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"測試會話: {self.summary['session_id']}",
            f"\n## 評分標準",
            "- 綜合評分 = 完成率×0.5 + 利用率×0.3 - 標準化等待時間×0.2",
            f"\n## 最優參數推薦",
            ""
        ]
        
        for robot_count in sorted(optimal_params.keys()):
            params = optimal_params[robot_count]
            report_lines.extend([
                f"### 機器人數量: {robot_count}",
                f"- **最優參數**: {params['parameter']}",
                f"- 綜合評分: {params['composite_score']:.3f}",
                f"- 訂單完成率: {params['completion_rate']:.1%}",
                f"- 平均等待時間: {params['avg_wait_time']:.1f} ticks",
                f"- 機器人利用率: {params['robot_utilization']:.1%}",
                ""
            ])
        
        # 添加詳細數據表格
        report_lines.extend([
            "\n## 詳細數據表格",
            f"\n### 所有測試結果（按綜合評分排序）",
            ""
        ])
        
        # 創建詳細數據表
        summary_df = df.groupby(['robot_count', 'parameter']).agg({
            'composite_score': 'mean',
            'completion_rate': 'mean',
            'avg_wait_time': 'mean',
            'robot_utilization': 'mean',
            'total_energy': 'mean'
        }).round(3)
        
        summary_df = summary_df.sort_values(['robot_count', 'composite_score'], 
                                          ascending=[True, False])
        
        # 轉換為 Markdown 表格
        report_lines.append("| 機器人數 | 參數 | 綜合評分 | 完成率 | 等待時間 | 利用率 | 總能耗 |")
        report_lines.append("|---------|------|---------|--------|----------|--------|--------|")
        
        for (robot_count, parameter), metrics in summary_df.iterrows():
            report_lines.append(
                f"| {robot_count} | {parameter} | "
                f"{metrics['composite_score']:.3f} | "
                f"{metrics['completion_rate']:.1%} | "
                f"{metrics['avg_wait_time']:.1f} | "
                f"{metrics['robot_utilization']:.1%} | "
                f"{metrics['total_energy']:.0f} |"
            )
        
        # 保存報告
        report_path = self.analysis_dir / f"{self.summary['test_type']}_optimal_parameters.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"最優參數報告已保存: {report_path}")
        return str(report_path)
    
    def _get_parameter_label(self) -> str:
        """獲取參數標籤"""
        if self.summary['test_type'] == 'time_based':
            return '時間配比 (水平:垂直)'
        else:
            return '隊列閾值'
    
    def _get_metric_label(self, metric: str) -> str:
        """獲取指標標籤"""
        labels = {
            'completion_rate': '完成率',
            'avg_wait_time': '平均等待時間',
            'robot_utilization': '利用率'
        }
        return labels.get(metric, metric)
    
    def _get_metric_title(self, metric: str) -> str:
        """獲取指標標題"""
        titles = {
            'completion_rate': '訂單完成率',
            'avg_wait_time': '平均等待時間',
            'robot_utilization': '機器人利用率'
        }
        return titles.get(metric, metric)
    
    def generate_all_analyses(self) -> Dict[str, str]:
        """生成所有分析"""
        results = {}
        
        try:
            # 生成參數比較圖表
            results['parameter_comparison'] = self.generate_parameter_comparison_chart()
            
            # 生成熱力圖分析
            results['heatmap_analysis'] = self.generate_heatmap_analysis()
            
            # 生成最優參數報告
            results['optimal_report'] = self.generate_optimal_parameter_report()
            
            self.logger.info("所有分析已完成")
            
        except Exception as e:
            self.logger.error(f"生成分析時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        return results


def main():
    """主函數，用於命令列執行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='基準模型參數分析')
    parser.add_argument('session_dir', help='測試會話目錄路徑')
    
    args = parser.parse_args()
    
    # 創建分析器
    analyzer = BaselineAnalyzer(args.session_dir)
    
    # 生成所有分析
    results = analyzer.generate_all_analyses()
    
    print("\n=== 基準模型分析完成 ===")
    for analysis_type, path in results.items():
        if path:
            print(f"{analysis_type}: {path}")


if __name__ == '__main__':
    main()