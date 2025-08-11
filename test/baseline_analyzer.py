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
        
        # 資料清洗與相容設定
        self.enable_cleaning: bool = True
        self.outliers_removed: list = []
        self.cleaning_stats: dict = {}

        # 載入測試摘要
        self.summary = self._load_summary()
        
    def _load_summary(self) -> Dict[str, Any]:
        """載入測試摘要"""
        # 首先嘗試在當前目錄查找
        summary_file = self.session_dir / 'baseline_test_summary.json'
        
        # 如果不存在，嘗試在上一層目錄查找
        if not summary_file.exists():
            summary_file = self.session_dir.parent / 'baseline_test_summary.json'
        
        # 如果還是不存在，生成一個基於現有數據的摘要
        if not summary_file.exists():
            self.logger.warning(f"找不到測試摘要檔案，嘗試從現有數據生成摘要")
            return self._generate_summary_from_data()
        
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.warning(f"測試摘要檔案格式錯誤: {e}")
            self.logger.warning(f"嘗試從現有數據重新生成摘要")
            return self._generate_summary_from_data()

    def _generate_summary_from_data(self) -> Dict[str, Any]:
        """從現有數據生成測試摘要"""
        # 收集所有測試結果
        results = []
        
        # 檢查是否有 workspaces 目錄（新格式）
        workspaces_dir = self.session_dir / 'workspaces'
        if workspaces_dir.exists():
            # 新格式：測試結果在 workspaces 子目錄中
            for workspace_dir in workspaces_dir.iterdir():
                if not workspace_dir.is_dir():
                    continue
                    
                # 尋找 results 目錄
                results_dir = workspace_dir / 'results'
                if results_dir.exists():
                    for test_dir in results_dir.iterdir():
                        if test_dir.is_dir():
                            eval_file = test_dir / 'evaluation_results.json'
                            if eval_file.exists():
                                result = self._extract_result_from_eval_file(eval_file, test_dir.name)
                                if result:
                                    results.append(result)
        else:
            # 舊格式：測試結果直接在 session_dir 下
            test_dirs = [d for d in self.session_dir.iterdir() if d.is_dir() and not d.name == 'analysis']
            
            for test_dir in test_dirs:
                # 尋找評估結果
                eval_file = test_dir / 'evaluation_results.json'
                if eval_file.exists():
                    result = self._extract_result_from_eval_file(eval_file, test_dir.name)
                    if result:
                        results.append(result)
        
        # 判斷測試類型
        test_type = 'unknown'
        if results:
            if results[0].get('controller') == 'time_based':
                test_type = 'time_based'
                # 收集所有不同的時間配比
                time_ratios = list(set(r.get('time_ratio', '') for r in results if 'time_ratio' in r))
            elif results[0].get('controller') == 'queue_based':
                test_type = 'queue_based'
                # 收集所有不同的隊列閾值
                queue_thresholds = list(set(r.get('queue_threshold', 0) for r in results if 'queue_threshold' in r))
        
        # 生成摘要
        summary = {
            'test_type': test_type,
            'session_id': self.session_dir.name,
            'total_tests': len(results),
            'completed_tests': len([r for r in results if r.get('status') == 'completed']),
            'failed_tests': len([r for r in results if r.get('status') != 'completed']),
            'output_dir': str(self.session_dir),
            'results': results
        }
        
        if test_type == 'time_based':
            summary['time_ratios'] = sorted(time_ratios) if 'time_ratios' in locals() else []
            summary['robot_counts'] = sorted(list(set(r['robot_count'] for r in results if 'robot_count' in r)))
        elif test_type == 'queue_based':
            summary['queue_thresholds'] = sorted(queue_thresholds) if 'queue_thresholds' in locals() else []
            summary['robot_counts'] = sorted(list(set(r['robot_count'] for r in results if 'robot_count' in r)))
        
        return summary
    
    def _extract_result_from_eval_file(self, eval_file: Path, test_id: str) -> Optional[Dict[str, Any]]:
        """從評估檔案中提取結果"""
        try:
            with open(eval_file, 'r', encoding='utf-8') as f:
                eval_data = json.load(f)
                
            # 解析測試 ID 來獲取參數
            parts = test_id.split('_')
            
            if test_id.startswith('tb_'):
                # Time-based 測試
                robot_count = int(parts[1][1:])  # r30 -> 30
                time_ratio = f"{parts[2][1:3]}:{parts[2][3:]}"  # t6040 -> 60:40
                run_index = int(parts[3][3:])  # run0 -> 0
                
                result = {
                    'test_id': test_id,
                    'robot_count': robot_count,
                    'controller': 'time_based',
                    'time_ratio': time_ratio,
                    'run_index': run_index,
                    'status': 'completed'
                }
            elif test_id.startswith('qb_'):
                # Queue-based 測試
                robot_count = int(parts[1][1:])  # r30 -> 30
                queue_threshold = int(parts[2][1:])  # q3 -> 3
                run_index = int(parts[3][3:])  # run0 -> 0
                
                result = {
                    'test_id': test_id,
                    'robot_count': robot_count,
                    'controller': 'queue_based',
                    'queue_threshold': queue_threshold,
                    'run_index': run_index,
                    'status': 'completed'
                }
            else:
                return None
            
            # 從評估結果中提取關鍵指標
            if eval_data.get('results'):
                metrics = eval_data['results'][0]
                result['completed_orders'] = metrics.get('completed_orders', 0)
                result['total_orders'] = metrics.get('total_orders', 0)
                result['completion_rate'] = metrics.get('completion_rate', 0)
                result['avg_wait_time'] = metrics.get('avg_wait_time', 0)
                # 相容舊資料：>1 視為舊單位（步數/秒），乘 0.15 校正到 0~1
                ru = metrics.get('robot_utilization', 0)
                result['robot_utilization'] = (ru * 0.15) if isinstance(ru, (int, float)) and ru > 1 else ru
                result['total_energy'] = metrics.get('total_energy', 0)
                # 優先用 evaluation 的 energy_per_order；若不存在，fallback 由 total_energy/完成訂單
                epo = metrics.get('energy_per_order', None)
                if epo is None or (isinstance(epo, float) and np.isnan(epo)):
                    co = result.get('completed_orders', 0)
                    result['energy_per_order'] = (result['total_energy'] / co) if co else np.nan
                else:
                    result['energy_per_order'] = epo
            
            return result
            
        except Exception as e:
            self.logger.warning(f"無法從 {eval_file} 提取結果: {e}")
            return None
    
    def _load_all_results(self) -> pd.DataFrame:
        """載入所有測試結果並轉換為 DataFrame"""
        all_results = []
        
        # 檢查是否有結果
        if not self.summary.get('results'):
            self.logger.warning("沒有找到任何測試結果")
            # 返回空的 DataFrame，但包含所需的欄位
            return pd.DataFrame(columns=['test_id', 'robot_count', 'run_index', 'parameter', 
                                        'parameter_type', 'completion_rate', 'avg_wait_time', 
                                        'robot_utilization', 'total_energy', 'execution_time',
                                        'signal_switch_count', 'avg_traffic_rate', 'energy_per_order'])
        
        for result in self.summary['results']:
            if result.get('status') != 'completed':
                continue
                
            # 提取基本資訊
            test_record = {
                'test_id': result.get('test_id', ''),
                'robot_count': result.get('robot_count', 0),
                'run_index': result.get('run_index', 0),
            }
            
            # 根據測試類型提取參數
            if self.summary['test_type'] == 'time_based':
                test_record['parameter'] = result.get('time_ratio', '')
                test_record['parameter_type'] = 'time_ratio'
            else:  # queue_based
                test_record['parameter'] = str(result.get('queue_threshold', 0))
                test_record['parameter_type'] = 'queue_threshold'
            
            # 提取性能指標（包含所有可能的欄位）
            test_record['completed_orders'] = result.get('completed_orders', 0)
            test_record['total_orders'] = result.get('total_orders', 0)
            test_record['completion_rate'] = result.get('completion_rate', 0)
            test_record['avg_wait_time'] = result.get('avg_wait_time', 0)
            test_record['robot_utilization'] = result.get('robot_utilization', 0)
            test_record['total_energy'] = result.get('total_energy', 0)
            
            # 提取新的指標（如果存在）
            test_record['signal_switch_count'] = result.get('signal_switch_count', 0)
            test_record['avg_traffic_rate'] = result.get('avg_traffic_rate', 0)
            
            # energy_per_order 若缺失則以總能耗/完成訂單估算
            epo = result.get('energy_per_order', None)
            if epo is None or (isinstance(epo, float) and np.isnan(epo)):
                co = test_record['completed_orders']
                test_record['energy_per_order'] = (test_record['total_energy'] / co) if co else np.nan
            else:
                test_record['energy_per_order'] = epo
                
            test_record['execution_time'] = result.get('execution_time', 0)
            
            all_results.append(test_record)
        
        # 如果沒有結果，返回空的 DataFrame
        if not all_results:
            self.logger.warning("沒有找到任何完成的測試結果")
            return pd.DataFrame(columns=['test_id', 'robot_count', 'run_index', 'parameter', 
                                        'parameter_type', 'completion_rate', 'avg_wait_time', 
                                        'robot_utilization', 'total_energy', 'execution_time',
                                        'signal_switch_count', 'avg_traffic_rate', 'energy_per_order'])
        
        return pd.DataFrame(all_results)

    # --------------------- 資料清洗（與 CapacityAnalyzer 對齊的邏輯，門檻同等嚴格） ---------------------
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """對 baseline 結果進行清洗，群組為 (robot_count, parameter)。"""
        self.outliers_removed = []
        self.cleaning_stats = {}

        if df.empty:
            return df

        df_work = df.copy()

        # 1) 訂單生成異常（全域）：total_orders < 0.75 × max_total_orders
        if 'total_orders' in df_work.columns and df_work['total_orders'].notna().any():
            max_total_orders = df_work['total_orders'].max()
            order_threshold = max_total_orders * 0.75
            mask_order = df_work['total_orders'] < order_threshold
        else:
            mask_order = pd.Series(False, index=df_work.index)
            order_threshold = np.nan

        # 2) 群組內異常（每個 robot_count×parameter，n≥5 用 trimmed-mean 門檻 0.85）
        mask_group = pd.Series(False, index=df_work.index)
        group_keys = ['robot_count', 'parameter'] if 'parameter' in df_work.columns else ['robot_count']
        for keys, group in df_work.groupby(group_keys):
            if 'completed_orders' not in group.columns:
                continue
            n = len(group)
            if n >= 5:
                orders = group['completed_orders'].values
                trimmed_mean = np.mean(np.sort(orders)[1:-1]) if n > 2 else np.mean(orders)
                bad_idx = group[group['completed_orders'] < trimmed_mean * 0.85].index
                mask_group.loc[bad_idx] = True
                for idx in bad_idx:
                    row = df_work.loc[idx]
                    self.outliers_removed.append({
                        'robot_count': int(row.get('robot_count', 0)),
                        'parameter': row.get('parameter', ''),
                        'completed_orders': int(row.get('completed_orders', 0)),
                        'total_orders': int(row.get('total_orders', 0)),
                        'completion_rate': float(row.get('completion_rate', 0)),
                        'reason': f'群組內異常 (n={n}, 低於 trimmed-mean 的 85%)'
                    })

        # 3) 跨參數的一般性能異常（同一 robot_count）
        mask_perf = pd.Series(False, index=df_work.index)
        if 'completed_orders' in df_work.columns:
            med_by_robot = df_work.groupby('robot_count')['completed_orders'].median()
            for rc, group in df_work.groupby('robot_count'):
                median_orders = med_by_robot.get(rc, np.nan)
                if np.isnan(median_orders):
                    continue
                cond = (group['completion_rate'] < 0.70) & (group['completed_orders'] < median_orders * 0.5)
                bad_idx = group[cond].index
                mask_perf.loc[bad_idx] = True
                for idx in bad_idx:
                    row = df_work.loc[idx]
                    self.outliers_removed.append({
                        'robot_count': int(row.get('robot_count', 0)),
                        'parameter': row.get('parameter', ''),
                        'completed_orders': int(row.get('completed_orders', 0)),
                        'total_orders': int(row.get('total_orders', 0)),
                        'completion_rate': float(row.get('completion_rate', 0)),
                        'reason': '一般性能異常 (完成率<70% 且 完成數低於組內中位數的50%)'
                    })

        # 合併遮罩
        combined_mask = mask_order | mask_group | mask_perf
        cleaned_df = df_work[~combined_mask].copy()

        # 彙總清洗統計（overall 與 by robot_count）
        self.cleaning_stats['overall'] = {
            'original_count': int(len(df_work)),
            'cleaned_count': int(len(cleaned_df)),
            'removed_count': int(len(df_work) - len(cleaned_df)),
            'removal_rate': (len(df_work) - len(cleaned_df)) / len(df_work) * 100,
            'order_threshold': order_threshold
        }
        for rc, group in df_work.groupby('robot_count'):
            cleaned_group = cleaned_df[cleaned_df['robot_count'] == rc]
            self.cleaning_stats[int(rc)] = {
                'original_count': int(len(group)),
                'cleaned_count': int(len(cleaned_group)),
                'removed_count': int(len(group) - len(cleaned_group)),
                'removal_rate': (len(group) - len(cleaned_group)) / len(group) * 100 if len(group) > 0 else 0,
                'median_before': float(group['completed_orders'].median()) if 'completed_orders' in group else np.nan,
                'median_after': float(cleaned_group['completed_orders'].median()) if 'completed_orders' in cleaned_group and len(cleaned_group) > 0 else np.nan,
            }

        return cleaned_df
    
    def generate_parameter_comparison_chart(self) -> str:
        """生成參數比較圖表（增強版）"""
        df = self._load_all_results()
        # 清洗（若啟用）
        if self.enable_cleaning and not df.empty:
            df = self._clean_data(df)
        
        # 檢查是否有數據
        if df.empty:
            self.logger.warning("沒有數據可以生成圖表")
            # 創建一個空圖表說明沒有數據
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            ax.text(0.5, 0.5, '沒有找到測試數據\n請先執行基準測試', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=20)
            ax.set_xticks([])
            ax.set_yticks([])
            
            chart_path = self.analysis_dir / f"{self.summary.get('test_type', 'unknown')}_parameter_comparison.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"參數比較圖表已保存: {chart_path}")
            return str(chart_path)
        
        # 檢查可用的欄位
        available_columns = df.columns.tolist()
        has_new_metrics = all(col in available_columns for col in ['signal_switch_count', 'avg_traffic_rate'])
        
        # 根據可用欄位決定佈局
        if has_new_metrics:
            fig, axes = plt.subplots(3, 2, figsize=(16, 18))
            fig.suptitle(f"{self.summary['test_type'].replace('_', ' ').title()} 參數掃描結果分析（增強版）", 
                         fontsize=16, fontweight='bold')
        else:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f"{self.summary['test_type'].replace('_', ' ').title()} 參數掃描結果分析", 
                         fontsize=16, fontweight='bold')
        
        # 獲取唯一的機器人數量
        robot_counts = sorted(df['robot_count'].unique())
        
        # 定義顏色映射
        colors = plt.cm.Set1(np.linspace(0, 1, len(robot_counts)))
        
        # 將 axes 展平為一維數組
        axes_flat = axes.flatten() if has_new_metrics else axes.flatten()
        plot_idx = 0
        
        # 1. 完成率 vs 參數（顯示樣本數 n）
        ax1 = axes_flat[plot_idx]
        plot_idx += 1
        for i, robot_count in enumerate(robot_counts):
            subset = df[df['robot_count'] == robot_count]
            # 計算每個參數的平均值和標準差
            grouped = subset.groupby('parameter').agg({
                'completion_rate': ['mean', 'std']
            })
            counts = subset.groupby('parameter').size()
            
            x = grouped.index
            y = grouped['completion_rate']['mean']
            yerr = grouped['completion_rate']['std']
            
            ax1.errorbar(x, y, yerr=yerr, marker='o', label=f'{robot_count} 機器人',
                        color=colors[i], capsize=5, markersize=8)
            # 在每個點上標註 n
            for xi, yi in zip(x, y):
                n = int(counts.get(xi, 0))
                ax1.text(xi, yi + 0.01, f'n={n}', ha='center', va='bottom', fontsize=8)
        
        ax1.set_xlabel(self._get_parameter_label())
        ax1.set_ylabel('訂單完成率')
        ax1.set_title('訂單完成率 vs 參數設定')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1.1)
        
        # 2. 平均等待時間 vs 參數（如果有此欄位）
        if 'avg_wait_time' in available_columns:
            ax2 = axes_flat[plot_idx]
            plot_idx += 1
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
        ax3 = axes_flat[plot_idx]
        plot_idx += 1
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
        
        # 4. 能源效率 vs 參數（每訂單能源消耗，越低越好）
        if 'energy_per_order' in available_columns:
            ax4 = axes_flat[plot_idx]
            plot_idx += 1
            for i, robot_count in enumerate(robot_counts):
                subset = df[df['robot_count'] == robot_count]
                
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
        
        # 5. 信號切換次數 vs 參數（如果有新指標）
        if has_new_metrics and plot_idx < len(axes_flat):
            ax5 = axes_flat[plot_idx]
            plot_idx += 1
            for i, robot_count in enumerate(robot_counts):
                subset = df[df['robot_count'] == robot_count]
                grouped = subset.groupby('parameter').agg({
                    'signal_switch_count': ['mean', 'std']
                })
                
                x = grouped.index
                y = grouped['signal_switch_count']['mean']
                yerr = grouped['signal_switch_count']['std']
                
                ax5.errorbar(x, y, yerr=yerr, marker='s', label=f'{robot_count} 機器人',
                            color=colors[i], capsize=5, markersize=8)
            
            ax5.set_xlabel(self._get_parameter_label())
            ax5.set_ylabel('信號切換次數')
            ax5.set_title('交通控制穩定性 vs 參數設定')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # 6. 平均交通流率 vs 參數（如果有新指標）
        if has_new_metrics and plot_idx < len(axes_flat):
            ax6 = axes_flat[plot_idx]
            plot_idx += 1
            for i, robot_count in enumerate(robot_counts):
                subset = df[df['robot_count'] == robot_count]
                grouped = subset.groupby('parameter').agg({
                    'avg_traffic_rate': ['mean', 'std']
                })
                
                x = grouped.index
                y = grouped['avg_traffic_rate']['mean']
                yerr = grouped['avg_traffic_rate']['std']
                
                ax6.errorbar(x, y, yerr=yerr, marker='v', label=f'{robot_count} 機器人',
                            color=colors[i], capsize=5, markersize=8)
            
            ax6.set_xlabel(self._get_parameter_label())
            ax6.set_ylabel('平均交通流率')
            ax6.set_title('交通流暢度 vs 參數設定')
            ax6.legend()
            ax6.grid(True, alpha=0.3)
        
        # 調整佈局
        plt.tight_layout()
        
        # 保存圖表
        chart_path = self.analysis_dir / f"{self.summary['test_type']}_parameter_comparison.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"參數比較圖表已保存: {chart_path}")
        return str(chart_path)
    
    def generate_heatmap_analysis(self) -> str:
        """生成熱力圖分析（增強版）"""
        df = self._load_all_results()
        
        # 檢查是否有數據
        if df.empty:
            self.logger.warning("沒有數據可以生成熱力圖")
            # 創建一個空圖表說明沒有數據
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            ax.text(0.5, 0.5, '沒有找到測試數據\n請先執行基準測試', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=20)
            ax.set_xticks([])
            ax.set_yticks([])
            
            chart_path = self.analysis_dir / f"{self.summary.get('test_type', 'unknown')}_heatmap_analysis.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"熱力圖分析已保存: {chart_path}")
            return str(chart_path)
        
        # 檢查可用的欄位
        available_columns = df.columns.tolist()
        
        # 定義所有可能的指標
        all_metrics = ['completion_rate', 'energy_per_order', 'signal_switch_count', 
                      'avg_traffic_rate', 'robot_utilization', 'total_energy', 'avg_wait_time']
        
        # 只使用實際存在的指標
        metrics = [m for m in all_metrics if m in available_columns]
        
        if not metrics:
            self.logger.warning("沒有找到可用的指標欄位")
            return ""
        
        # 根據指標數量決定佈局
        n_metrics = len(metrics)
        if n_metrics <= 3:
            rows, cols = 1, n_metrics
        elif n_metrics <= 6:
            rows, cols = 2, 3
        else:
            rows = (n_metrics + 2) // 3
            cols = 3
        
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 6.5, rows * 7))
        fig.suptitle(f"{self.summary['test_type'].replace('_', ' ').title()} 參數熱力圖分析", 
                     fontsize=16, fontweight='bold')
        
        # 如果只有一個子圖，確保 axes 是數組
        if n_metrics == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
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
            if metric in ['avg_wait_time', 'energy_per_order', 'signal_switch_count', 'total_energy']:
                cmap = 'YlOrRd_r'  # 反轉顏色，因為這些指標越低越好
            else:
                cmap = 'YlGn'  # 完成率、利用率、交通流率越高越好
            
            # 添加數值標註格式
            if metric in ['completion_rate', 'robot_utilization']:
                fmt = '.1%'  # 百分比格式
            elif metric == 'avg_traffic_rate':
                fmt = '.4f'  # 小數點後4位
            elif metric in ['signal_switch_count', 'total_energy']:
                fmt = '.0f'  # 整數
            else:
                fmt = '.1f'  # 一般格式
            
            sns.heatmap(pivot, annot=True, fmt=fmt, cmap=cmap, 
                       cbar_kws={'label': self._get_metric_label(metric)},
                       ax=ax)
            
            ax.set_title(self._get_metric_title(metric))
            ax.set_xlabel('機器人數量')
            ax.set_ylabel(self._get_parameter_label())
            
            # 旋轉 x 軸標籤以避免重疊
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        
        # 隱藏多餘的子圖
        for idx in range(n_metrics, len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        
        # 保存圖表
        chart_path = self.analysis_dir / f"{self.summary['test_type']}_heatmap_analysis.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"熱力圖分析已保存: {chart_path}")
        return str(chart_path)
    
    def generate_optimal_parameter_report(self) -> str:
        """生成最優參數報告（增強版）"""
        df = self._load_all_results()
        
        # 生成報告
        report_lines = [
            f"# {self.summary.get('test_type', 'Unknown').replace('_', ' ').title()} 最優參數分析報告",
            f"\n生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"測試會話: {self.summary.get('session_id', 'Unknown')}",
        ]
        
        # 檢查是否有數據
        if df.empty:
            report_lines.extend([
                "\n## 沒有找到測試數據",
                "請先執行基準測試以生成分析數據。"
            ])
            
            # 保存報告
            report_path = self.analysis_dir / f"{self.summary.get('test_type', 'unknown')}_optimal_parameters.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            self.logger.info(f"最優參數報告已保存: {report_path}")
            return str(report_path)
        
        # 檢查可用的欄位
        available_columns = df.columns.tolist()
        has_new_metrics = all(col in available_columns for col in ['signal_switch_count', 'avg_traffic_rate'])
        
        # 計算基本綜合分數（適用於舊數據）
        # 分數 = 完成率 * 0.5 + 利用率 * 0.3 - 標準化等待時間 * 0.2
        if 'avg_wait_time' in available_columns and df['avg_wait_time'].max() > 0:
            df['wait_time_normalized'] = df['avg_wait_time'] / df['avg_wait_time'].max()
        else:
            df['wait_time_normalized'] = 0
            
        df['composite_score'] = (
            df['completion_rate'] * 0.5 + 
            df['robot_utilization'] * 0.3 - 
            df['wait_time_normalized'] * 0.2
        )
        
        # 如果有新指標，計算更多綜合分數
        if has_new_metrics:
            # 1. 效率優先分數（重視完成率和能源效率）
            if 'energy_per_order' in available_columns and df['energy_per_order'].max() > 0:
                df['energy_normalized'] = 1 - (df['energy_per_order'] / df['energy_per_order'].max())
            else:
                df['energy_normalized'] = 0
                
            df['efficiency_score'] = (
                df['completion_rate'] * 0.5 + 
                df['energy_normalized'] * 0.5
            )
            
            # 2. 穩定性優先分數（重視信號切換少和交通流暢）
            if df['signal_switch_count'].max() > 0:
                df['signal_normalized'] = 1 - (df['signal_switch_count'] / df['signal_switch_count'].max())
            else:
                df['signal_normalized'] = 0
                
            if df['avg_traffic_rate'].max() > 0:
                df['traffic_normalized'] = df['avg_traffic_rate'] / df['avg_traffic_rate'].max()
            else:
                df['traffic_normalized'] = 0
                
            df['stability_score'] = (
                df['completion_rate'] * 0.3 + 
                df['signal_normalized'] * 0.4 +
                df['traffic_normalized'] * 0.3
            )
            
            # 3. 綜合平衡分數
            df['balanced_score'] = (
                df['completion_rate'] * 0.4 + 
                df.get('energy_normalized', 0) * 0.3 +
                df.get('signal_normalized', 0) * 0.2 +
                df['robot_utilization'] * 0.1
            )
        
        # 找出每個機器人數量的最優參數
        optimal_params = {}
        for robot_count in sorted(df['robot_count'].unique()):
            subset = df[df['robot_count'] == robot_count]
            grouped = subset.groupby('parameter').agg({
                'composite_score': 'mean',
                'completion_rate': 'mean',
                'robot_utilization': 'mean'
            })
            
            # 添加可用的其他指標
            if 'avg_wait_time' in available_columns:
                grouped['avg_wait_time'] = subset.groupby('parameter')['avg_wait_time'].mean()
            if 'energy_per_order' in available_columns:
                grouped['energy_per_order'] = subset.groupby('parameter')['energy_per_order'].mean()
            if 'total_energy' in available_columns:
                grouped['total_energy'] = subset.groupby('parameter')['total_energy'].mean()
            
            # 找出最高分數的參數
            if len(grouped) > 0:
                best_param = grouped['composite_score'].idxmax()
                best_metrics = grouped.loc[best_param]
                
                optimal_params[robot_count] = {
                    'parameter': best_param,
                    'composite_score': best_metrics['composite_score'],
                    'completion_rate': best_metrics['completion_rate'],
                    'robot_utilization': best_metrics['robot_utilization']
                }
                
                # 添加可選指標
                if 'avg_wait_time' in grouped.columns:
                    optimal_params[robot_count]['avg_wait_time'] = best_metrics['avg_wait_time']
                if 'energy_per_order' in grouped.columns:
                    optimal_params[robot_count]['energy_per_order'] = best_metrics['energy_per_order']
        
        # 添加評分標準和最優參數推薦
        report_lines.extend([
            f"\n## 評分標準",
            "- 綜合評分 = 完成率×0.5 + 利用率×0.3 - 標準化等待時間×0.2",
        ])
        
        if has_new_metrics:
            report_lines.extend([
                "- 效率優先分數 = 完成率×0.5 + 能源效率×0.5",
                "- 穩定性優先分數 = 完成率×0.3 + 信號穩定性×0.4 + 交通流暢度×0.3",
                "- 綜合平衡分數 = 完成率×0.4 + 能源效率×0.3 + 信號穩定性×0.2 + 機器人利用率×0.1",
            ])
        
        report_lines.extend([
            f"\n## 最優參數推薦",
            ""
        ])
        
        for robot_count in sorted(optimal_params.keys()):
            params = optimal_params[robot_count]
            report_lines.extend([
                f"### 機器人數量: {robot_count}",
                f"- **最優參數**: {params['parameter']}",
                f"- 綜合評分: {params['composite_score']:.3f}",
                f"- 訂單完成率: {params['completion_rate']:.1%}",
            ])
            
            if 'avg_wait_time' in params:
                report_lines.append(f"- 平均等待時間: {params['avg_wait_time']:.1f} ticks")
            
            report_lines.append(f"- 機器人利用率: {params['robot_utilization']:.1%}")
            
            if 'energy_per_order' in params:
                report_lines.append(f"- 每訂單能耗: {params['energy_per_order']:.1f}")
            
            report_lines.append("")
        
        # 添加詳細數據表格
        report_lines.extend([
            "\n## 詳細數據表格",
            f"\n### 所有測試結果（按綜合評分排序）",
            ""
        ])
        
        # 創建詳細數據表
        agg_dict = {
            'composite_score': 'mean',
            'completion_rate': 'mean',
            'robot_utilization': 'mean'
        }
        
        # 添加可選欄位
        if 'avg_wait_time' in available_columns:
            agg_dict['avg_wait_time'] = 'mean'
        if 'total_energy' in available_columns:
            agg_dict['total_energy'] = 'mean'
        if 'energy_per_order' in available_columns:
            agg_dict['energy_per_order'] = 'mean'
        
        summary_df = df.groupby(['robot_count', 'parameter']).agg(agg_dict).round(3)
        
        summary_df = summary_df.sort_values(['robot_count', 'composite_score'], 
                                          ascending=[True, False])
        
        # 轉換為 Markdown 表格
        header = "| 機器人數 | 參數 | 綜合評分 | 完成率 | 利用率"
        separator = "|---------|------|---------|--------|--------"
        
        if 'avg_wait_time' in summary_df.columns:
            header += " | 等待時間"
            separator += "|----------"
        if 'energy_per_order' in summary_df.columns:
            header += " | 每訂單能耗"
            separator += "|------------"
        if 'total_energy' in summary_df.columns:
            header += " | 總能耗"
            separator += "|--------|"
        
        header += " |"
        separator += "|"
        
        report_lines.append(header)
        report_lines.append(separator)
        
        for (robot_count, parameter), metrics in summary_df.iterrows():
            row = f"| {robot_count} | {parameter} | "
            row += f"{metrics['composite_score']:.3f} | "
            row += f"{metrics['completion_rate']:.1%} | "
            row += f"{metrics['robot_utilization']:.1%}"
            
            if 'avg_wait_time' in metrics:
                row += f" | {metrics['avg_wait_time']:.1f}"
            if 'energy_per_order' in metrics:
                row += f" | {metrics['energy_per_order']:.1f}"
            if 'total_energy' in metrics:
                row += f" | {metrics['total_energy']:.0f}"
            
            row += " |"
            report_lines.append(row)
        
        # 保存報告
        report_path = self.analysis_dir / f"{self.summary.get('test_type', 'unknown')}_optimal_parameters.md"
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
            'robot_utilization': '利用率',
            'energy_per_order': '每訂單能耗',
            'signal_switch_count': '信號切換次數',
            'avg_traffic_rate': '平均交通流率',
            'total_energy': '總能源消耗'
        }
        return labels.get(metric, metric)
    
    def _get_metric_title(self, metric: str) -> str:
        """獲取指標標題"""
        titles = {
            'completion_rate': '訂單完成率',
            'avg_wait_time': '平均等待時間',
            'robot_utilization': '機器人利用率',
            'energy_per_order': '每訂單能源消耗',
            'signal_switch_count': '信號切換次數',
            'avg_traffic_rate': '平均交通流率',
            'total_energy': '總能源消耗'
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