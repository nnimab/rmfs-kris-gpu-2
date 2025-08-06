#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMFS 容量分析模組

負責收集、分析和視覺化容量測試結果，生成詳細的分析報告和圖表。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec
    import seaborn as sns
    # 設定中文字體
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    # 確保圖表中文顯示
    plt.rcParams['font.family'] = 'sans-serif'
    HAS_MATPLOTLIB = True
except ImportError:
    print("警告：找不到 matplotlib 或 seaborn，圖表功能將被禁用")
    HAS_MATPLOTLIB = False

from lib.logger import get_logger


class CapacityAnalyzer:
    """RMFS 容量分析器"""
    
    def __init__(self, results_dir: Path, logger: Optional[logging.Logger] = None):
        """
        初始化分析器
        
        Args:
            results_dir: 測試結果目錄
            logger: 日誌記錄器
        """
        self.results_dir = Path(results_dir)
        self.logger = logger or get_logger()
        
        # 檢查結果目錄是否存在
        if not self.results_dir.exists():
            raise FileNotFoundError(f"測試結果目錄不存在: {self.results_dir}")
        
        # 初始化數據存儲
        self.raw_data = {}
        self.processed_data = {}
        self.analysis_results = {}
        
        # 資料清洗相關屬性
        self.outliers_removed = []  # 記錄被移除的異常數據
        self.cleaning_stats = {}    # 清洗統計資訊
        self.enable_cleaning = True # 是否啟用資料清洗
        
        self.logger.info(f"容量分析器初始化完成，結果目錄: {self.results_dir}")
    
    def load_test_data(self) -> bool:
        """
        載入測試數據
        
        Returns:
            是否成功載入數據
        """
        try:
            # 尋找測試摘要檔案
            summary_files = list(self.results_dir.rglob("capacity_test_summary.json"))
            
            if not summary_files:
                self.logger.error("找不到測試摘要檔案")
                return False
            
            # 載入所有測試摘要
            for summary_file in summary_files:
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                    
                    test_id = summary.get('test_session_id', 'unknown')
                    self.raw_data[test_id] = summary
                    
                    self.logger.debug(f"已載入測試數據: {test_id}")
                    
                except Exception as e:
                    self.logger.error(f"載入測試摘要 {summary_file} 時發生錯誤: {e}")
            
            # 載入詳細的評估結果
            self._load_detailed_results()
            
            self.logger.info(f"成功載入 {len(self.raw_data)} 個測試會話的數據")
            return True
            
        except Exception as e:
            self.logger.error(f"載入測試數據時發生錯誤: {e}")
            return False
    
    def _load_detailed_results(self):
        """載入詳細的評估結果"""
        for test_id, summary in self.raw_data.items():
            try:
                # 尋找對應的詳細結果檔案
                results_files = list(self.results_dir.rglob("evaluation_results.json"))
                
                for results_file in results_files:
                    # 檢查是否屬於當前測試會話
                    if test_id in str(results_file.parent):
                        try:
                            with open(results_file, 'r', encoding='utf-8') as f:
                                detailed_results = json.load(f)
                            
                            if 'detailed_results' not in summary:
                                summary['detailed_results'] = []
                            
                            summary['detailed_results'].append(detailed_results)
                            
                        except Exception as e:
                            self.logger.warning(f"載入詳細結果 {results_file} 時發生錯誤: {e}")
                            
            except Exception as e:
                self.logger.warning(f"載入測試 {test_id} 的詳細結果時發生錯誤: {e}")
    
    def process_data(self) -> bool:
        """
        處理和分析數據
        
        Returns:
            是否成功處理數據
        """
        try:
            if not self.raw_data:
                self.logger.error("沒有可處理的數據")
                return False
            
            # 彙總所有測試結果
            all_results = []
            
            for test_id, summary in self.raw_data.items():
                for result in summary.get('all_results', []):
                    if result.get('status') == 'completed':
                        # 提取基本指標
                        processed_result = {
                            'test_id': test_id,
                            'robot_count': result['robot_count'],
                            'execution_time': result.get('execution_time', 0),
                            'test_ticks': summary.get('test_ticks', 0)
                        }
                        
                        # 提取評估結果中的指標
                        eval_results = result.get('evaluation_results')
                        if eval_results and isinstance(eval_results, dict):
                            # 檢查是否有 results 陣列
                            if 'results' in eval_results and eval_results['results']:
                                eval_data = eval_results['results'][0]
                            elif 'none' in eval_results:
                                eval_data = eval_results['none'][0] if eval_results['none'] else {}
                            else:
                                eval_data = eval_results
                            
                            processed_result.update({
                                'completed_orders': eval_data.get('completed_orders', 0),
                                'total_orders': eval_data.get('total_orders', 0),
                                'completion_rate': eval_data.get('completion_rate', 0),
                                'avg_wait_time': eval_data.get('avg_wait_time', 0),
                                'total_energy': eval_data.get('total_energy', 0),
                                'energy_per_order': eval_data.get('energy_per_order', 0),
                                'robot_utilization': eval_data.get('robot_utilization', 0),
                                'signal_switch_count': eval_data.get('signal_switch_count', 0),
                                'avg_traffic_rate': eval_data.get('avg_traffic_rate', 0)
                            })
                        
                        all_results.append(processed_result)
            
            # 轉換為 DataFrame 以便分析
            if all_results:
                df_original = pd.DataFrame(all_results)
                self.processed_data['df_original'] = df_original.copy()  # 保存原始數據供比較
                
                # 進行資料清洗（如果啟用）
                if self.enable_cleaning and len(df_original) > 0:
                    self.logger.info("開始資料清洗...")
                    df_cleaned = self._clean_data_by_group(df_original)
                    self.processed_data['df'] = df_cleaned
                    
                    # 記錄整體清洗統計
                    self.cleaning_stats['overall'] = {
                        'original_count': len(df_original),
                        'cleaned_count': len(df_cleaned),
                        'removed_count': len(df_original) - len(df_cleaned),
                        'removal_rate': (len(df_original) - len(df_cleaned)) / len(df_original) * 100
                    }
                else:
                    self.processed_data['df'] = df_original
                    self.logger.info("跳過資料清洗")
                
                self._calculate_analytics()
                
                self.logger.info(f"成功處理 {len(all_results)} 個測試結果")
                return True
            else:
                self.logger.error("沒有成功的測試結果可供分析")
                return False
                
        except Exception as e:
            self.logger.error(f"處理數據時發生錯誤: {e}")
            return False
    
    def _calculate_analytics(self):
        """計算分析指標"""
        df = self.processed_data['df']
        
        # 按機器人數量分組統計
        grouped = df.groupby('robot_count').agg({
            'completion_rate': ['mean', 'std'],
            'avg_wait_time': ['mean', 'std'],
            'total_energy': ['mean', 'std'],
            'energy_per_order': ['mean', 'std'],
            'robot_utilization': ['mean', 'std'],
            'execution_time': ['mean', 'std'],
            'completed_orders': ['mean', 'std'],
            'total_orders': ['mean', 'std']
        }).round(4)
        
        self.analysis_results['by_robot_count'] = grouped
        
        # 計算效率指標
        df['orders_per_robot'] = df['completed_orders'] / df['robot_count']
        df['energy_per_robot'] = df['total_energy'] / df['robot_count']
        df['throughput'] = df['completed_orders'] / (df['test_ticks'] / 1000)  # 每千 tick 完成的訂單數
        
        # 尋找最佳機器人數量
        best_completion_rate = df.loc[df['completion_rate'].idxmax()]
        best_efficiency = df.loc[df['orders_per_robot'].idxmax()]
        best_energy_efficiency = df.loc[df['energy_per_order'].idxmin()]
        
        self.analysis_results['best_performance'] = {
            'highest_completion_rate': {
                'robot_count': int(best_completion_rate['robot_count']),
                'completion_rate': float(best_completion_rate['completion_rate']),
                'completed_orders': int(best_completion_rate['completed_orders'])
            },
            'highest_efficiency': {
                'robot_count': int(best_efficiency['robot_count']),
                'orders_per_robot': float(best_efficiency['orders_per_robot']),
                'completion_rate': float(best_efficiency['completion_rate'])
            },
            'best_energy_efficiency': {
                'robot_count': int(best_energy_efficiency['robot_count']),
                'energy_per_order': float(best_energy_efficiency['energy_per_order']),
                'completion_rate': float(best_energy_efficiency['completion_rate'])
            }
        }
        
        # 計算擴展性指標
        self._calculate_scalability_metrics(df)

    def _detect_outliers(self, df: pd.DataFrame, column: str = 'completed_orders', 
                        method: str = 'iqr', threshold: float = 1.5) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        檢測並標記異常數據
        
        Args:
            df: 數據框架
            column: 要檢測異常值的欄位
            method: 檢測方法 ('iqr' 或 'zscore')
            threshold: 閾值（IQR方法預設1.5，z-score方法預設3）
            
        Returns:
            (清理後的數據, 被移除的異常數據)
        """
        df_copy = df.copy()
        
        if method == 'iqr':
            # 使用四分位數範圍（IQR）方法
            Q1 = df_copy[column].quantile(0.25)
            Q3 = df_copy[column].quantile(0.75)
            IQR = Q3 - Q1
            
            # 定義異常值範圍
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            # 標記異常值
            outliers_mask = (df_copy[column] < lower_bound) | (df_copy[column] > upper_bound)
            
            self.logger.info(f"IQR方法檢測 {column}: Q1={Q1:.2f}, Q3={Q3:.2f}, IQR={IQR:.2f}")
            self.logger.info(f"異常值範圍: < {lower_bound:.2f} 或 > {upper_bound:.2f}")
            
        elif method == 'zscore':
            # 使用Z-score方法
            mean = df_copy[column].mean()
            std = df_copy[column].std()
            z_scores = np.abs((df_copy[column] - mean) / std)
            outliers_mask = z_scores > threshold
            
            self.logger.info(f"Z-score方法檢測 {column}: mean={mean:.2f}, std={std:.2f}")
        
        else:
            raise ValueError(f"不支援的檢測方法: {method}")
        
        # 分離正常數據和異常數據
        clean_df = df_copy[~outliers_mask]
        outliers_df = df_copy[outliers_mask]
        
        if len(outliers_df) > 0:
            self.logger.warning(f"檢測到 {len(outliers_df)} 筆異常數據 ({len(outliers_df)/len(df_copy)*100:.1f}%)")
            
            # 記錄異常數據詳情
            for idx, row in outliers_df.iterrows():
                self.logger.debug(f"異常數據: 機器人={row['robot_count']}, {column}={row[column]}")
        
        return clean_df, outliers_df
    
    def _clean_data_by_group(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按機器人數量分組進行資料清洗
        
        Args:
            df: 原始數據框架
            
        Returns:
            清理後的數據框架
        """
        cleaned_dfs = []
        total_removed = 0
        
        # 按機器人數量分組
        for robot_count, group_df in df.groupby('robot_count'):
            if len(group_df) < 3:
                # 數據太少，不進行清洗
                cleaned_dfs.append(group_df)
                self.logger.info(f"機器人數量 {robot_count}: 數據量太少({len(group_df)}筆)，跳過清洗")
                continue
            
            # 檢測完成訂單數的異常值
            clean_df, outliers_df = self._detect_outliers(group_df, 'completed_orders')
            
            # 如果移除異常值後數據太少，使用較寬鬆的標準重新檢測
            if len(clean_df) < 3 and len(group_df) >= 5:
                self.logger.info(f"機器人數量 {robot_count}: 使用較寬鬆的標準重新檢測")
                clean_df, outliers_df = self._detect_outliers(group_df, 'completed_orders', threshold=2.0)
            
            # 記錄被移除的數據
            if len(outliers_df) > 0:
                for _, outlier in outliers_df.iterrows():
                    self.outliers_removed.append({
                        'robot_count': int(outlier['robot_count']),
                        'completed_orders': int(outlier['completed_orders']),
                        'total_orders': int(outlier['total_orders']),
                        'completion_rate': float(outlier['completion_rate']),
                        'reason': f'完成訂單數異常 (組內平均: {group_df["completed_orders"].mean():.1f})'
                    })
                
                total_removed += len(outliers_df)
            
            cleaned_dfs.append(clean_df)
            
            # 記錄清洗統計
            if robot_count not in self.cleaning_stats:
                self.cleaning_stats[robot_count] = {}
            
            self.cleaning_stats[robot_count] = {
                'original_count': len(group_df),
                'cleaned_count': len(clean_df),
                'removed_count': len(outliers_df),
                'removal_rate': len(outliers_df) / len(group_df) * 100 if len(group_df) > 0 else 0,
                'mean_before': group_df['completed_orders'].mean(),
                'mean_after': clean_df['completed_orders'].mean() if len(clean_df) > 0 else 0,
                'std_before': group_df['completed_orders'].std(),
                'std_after': clean_df['completed_orders'].std() if len(clean_df) > 0 else 0
            }
        
        # 合併清理後的數據
        if cleaned_dfs:
            cleaned_df = pd.concat(cleaned_dfs, ignore_index=True)
            self.logger.info(f"資料清洗完成: 原始 {len(df)} 筆，清理後 {len(cleaned_df)} 筆，移除 {total_removed} 筆")
            return cleaned_df
        else:
            return df
    
    def _calculate_scalability_metrics(self, df: pd.DataFrame):
        """計算擴展性指標"""
        # 按機器人數量排序
        sorted_df = df.sort_values('robot_count')
        
        scalability_metrics = {
            'linear_scalability': [],
            'efficiency_decline': [],
            'capacity_saturation': False
        }
        
        # 計算線性擴展性
        robot_counts = sorted_df['robot_count'].unique()
        for i, count in enumerate(robot_counts[1:], 1):
            prev_count = robot_counts[i-1]
            
            current_throughput = sorted_df[sorted_df['robot_count'] == count]['throughput'].mean()
            prev_throughput = sorted_df[sorted_df['robot_count'] == prev_count]['throughput'].mean()
            
            expected_throughput = prev_throughput * (count / prev_count)  # 理想線性擴展
            actual_ratio = current_throughput / expected_throughput if expected_throughput > 0 else 0
            
            scalability_metrics['linear_scalability'].append({
                'robot_count': count,
                'scalability_ratio': actual_ratio,
                'throughput': current_throughput
            })
        
        # 檢測容量飽和
        completion_rates = [sorted_df[sorted_df['robot_count'] == count]['completion_rate'].mean() 
                          for count in robot_counts]
        
        # 如果最後兩個數據點的完成率差距小於 1%，認為出現容量飽和
        if len(completion_rates) >= 2 and abs(completion_rates[-1] - completion_rates[-2]) < 0.01:
            scalability_metrics['capacity_saturation'] = True
            scalability_metrics['saturation_point'] = robot_counts[-2]
        
        self.analysis_results['scalability'] = scalability_metrics
    
    def generate_charts(self) -> List[str]:
        """
        生成分析圖表
        
        Returns:
            生成的圖表檔案路徑列表
        """
        if not HAS_MATPLOTLIB:
            self.logger.warning("matplotlib 不可用，跳過圖表生成")
            return []
        
        if 'df' not in self.processed_data:
            self.logger.error("沒有處理過的數據，無法生成圖表")
            return []
        
        chart_files = []
        df = self.processed_data['df']
        
        # 創建圖表輸出目錄
        charts_dir = self.results_dir / 'charts'
        charts_dir.mkdir(exist_ok=True)
        
        try:
            # 1. 容量-性能關係圖
            chart_files.append(self._create_capacity_performance_chart(df, charts_dir))
            
            # 2. 效率分析圖
            chart_files.append(self._create_efficiency_chart(df, charts_dir))
            
            # 3. 能源消耗分析圖
            chart_files.append(self._create_energy_chart(df, charts_dir))
            
            # 4. 擴展性分析圖
            chart_files.append(self._create_scalability_chart(df, charts_dir))
            
            # 5. 綜合儀表板
            chart_files.append(self._create_dashboard(df, charts_dir))
            
            # 6. 資料清洗比較圖（如果有進行清洗）
            if self.cleaning_stats and self.enable_cleaning:
                chart_files.append(self._create_cleaning_comparison_chart(charts_dir))
            
            self.logger.info(f"成功生成 {len([f for f in chart_files if f])} 個圖表")
            
        except Exception as e:
            self.logger.error(f"生成圖表時發生錯誤: {e}")
        
        return [f for f in chart_files if f]  # 過濾掉 None 值  # 過濾掉 None 值
    
    def _create_capacity_performance_chart(self, df: pd.DataFrame, output_dir: Path) -> Optional[str]:
        """創建容量-性能關係圖"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 按機器人數量分組
            grouped = df.groupby('robot_count').agg({
                'completion_rate': 'mean',
                'completed_orders': 'mean',
                'avg_wait_time': 'mean',
                'throughput': 'mean'
            })
            
            robot_counts = grouped.index
            
            # 完成率 vs 機器人數量
            ax1.plot(robot_counts, grouped['completion_rate'], 'bo-', linewidth=2, markersize=8)
            ax1.set_xlabel('機器人數量')
            ax1.set_ylabel('訂單完成率')
            ax1.set_title('完成率 vs 機器人數量 (平均值)')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 1.1)
            
            # 完成訂單數 vs 機器人數量
            ax2.plot(robot_counts, grouped['completed_orders'], 'go-', linewidth=2, markersize=8)
            ax2.set_xlabel('機器人數量')
            ax2.set_ylabel('完成訂單數')
            ax2.set_title('完成訂單數 vs 機器人數量 (平均值)')
            ax2.grid(True, alpha=0.3)
            
            # 平均等待時間 vs 機器人數量
            ax3.plot(robot_counts, grouped['avg_wait_time'], 'ro-', linewidth=2, markersize=8)
            ax3.set_xlabel('機器人數量')
            ax3.set_ylabel('平均等待時間')
            ax3.set_title('平均等待時間 vs 機器人數量 (各配置平均值)')
            ax3.grid(True, alpha=0.3)
            
            # 系統吞吐量 vs 機器人數量
            ax4.plot(robot_counts, grouped['throughput'], 'mo-', linewidth=2, markersize=8)
            ax4.set_xlabel('機器人數量')
            ax4.set_ylabel('吞吐量 (訂單/千tick)')
            ax4.set_title('系統吞吐量 vs 機器人數量 (平均值)')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            chart_file = output_dir / 'capacity_performance.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            self.logger.error(f"創建容量-性能圖表時發生錯誤: {e}")
            return None
    
    def _create_efficiency_chart(self, df: pd.DataFrame, output_dir: Path) -> Optional[str]:
        """創建效率分析圖"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 計算效率指標
            df_efficiency = df.copy()
            df_efficiency['orders_per_robot'] = df_efficiency['completed_orders'] / df_efficiency['robot_count']
            
            grouped = df_efficiency.groupby('robot_count').agg({
                'orders_per_robot': 'mean',
                'robot_utilization': 'mean'
            })
            
            robot_counts = grouped.index
            
            # 每機器人完成訂單數
            ax1.bar(robot_counts, grouped['orders_per_robot'], color='skyblue', alpha=0.7)
            ax1.set_xlabel('機器人數量')
            ax1.set_ylabel('每機器人完成訂單數')
            ax1.set_title('機器人效率分析 (平均值)')
            ax1.grid(True, alpha=0.3)
            
            # 添加數值標籤
            for i, v in enumerate(grouped['orders_per_robot']):
                ax1.text(robot_counts[i], v + 0.1, f'{v:.1f}', ha='center', va='bottom')
            
            # 機器人利用率
            ax2.bar(robot_counts, grouped['robot_utilization'], color='lightcoral', alpha=0.7)
            ax2.set_xlabel('機器人數量')
            ax2.set_ylabel('機器人利用率')
            ax2.set_title('機器人利用率分析 (平均值)')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 1.1)
            
            # 添加數值標籤
            for i, v in enumerate(grouped['robot_utilization']):
                ax2.text(robot_counts[i], v + 0.02, f'{v:.2f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            chart_file = output_dir / 'efficiency_analysis.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            self.logger.error(f"創建效率圖表時發生錯誤: {e}")
            return None
    
    def _create_energy_chart(self, df: pd.DataFrame, output_dir: Path) -> Optional[str]:
        """創建能源消耗分析圖"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            grouped = df.groupby('robot_count').agg({
                'total_energy': 'mean',
                'energy_per_order': 'mean'
            })
            
            robot_counts = grouped.index
            
            # 總能源消耗
            ax1.plot(robot_counts, grouped['total_energy'], 'o-', color='orange', linewidth=2, markersize=8)
            ax1.set_xlabel('機器人數量')
            ax1.set_ylabel('總能源消耗')
            ax1.set_title('總能源消耗 vs 機器人數量 (平均值)')
            ax1.grid(True, alpha=0.3)
            
            # 每訂單能源消耗
            ax2.plot(robot_counts, grouped['energy_per_order'], 'o-', color='red', linewidth=2, markersize=8)
            ax2.set_xlabel('機器人數量')
            ax2.set_ylabel('每訂單能源消耗')
            ax2.set_title('能源效率 vs 機器人數量 (平均值)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            chart_file = output_dir / 'energy_analysis.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            self.logger.error(f"創建能源圖表時發生錯誤: {e}")
            return None
    
    def _create_scalability_chart(self, df: pd.DataFrame, output_dir: Path) -> Optional[str]:
        """創建擴展性分析圖"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 線性擴展性分析
            scalability = self.analysis_results.get('scalability', {})
            linear_data = scalability.get('linear_scalability', [])
            
            if linear_data:
                robot_counts = [item['robot_count'] for item in linear_data]
                ratios = [item['scalability_ratio'] for item in linear_data]
                
                bars = ax1.bar(robot_counts, ratios, color='lightgreen', alpha=0.7)
                ax1.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='理想線性擴展')
                ax1.set_xlabel('機器人數量')
                ax1.set_ylabel('擴展性比率')
                ax1.set_title('線性擴展性分析 (基於平均值)')
                ax1.grid(True, alpha=0.3)
                ax1.legend()
                
                # 添加數值標籤
                for bar, ratio in zip(bars, ratios):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{ratio:.2f}', ha='center', va='bottom')
            
            # 吞吐量增長率
            df_sorted = df.sort_values('robot_count')
            grouped = df_sorted.groupby('robot_count')['throughput'].mean()
            
            growth_rates = []
            robot_counts_growth = list(grouped.index[1:])
            
            for i in range(1, len(grouped)):
                current = grouped.iloc[i]
                previous = grouped.iloc[i-1]
                growth_rate = ((current - previous) / previous) * 100 if previous > 0 else 0
                growth_rates.append(growth_rate)
            
            if growth_rates:
                ax2.bar(robot_counts_growth, growth_rates, color='skyblue', alpha=0.7)
                ax2.set_xlabel('機器人數量')
                ax2.set_ylabel('吞吐量增長率 (%)')
                ax2.set_title('吞吐量增長率分析 (基於平均值)')
                ax2.grid(True, alpha=0.3)
                ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            plt.tight_layout()
            
            chart_file = output_dir / 'scalability_analysis.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            self.logger.error(f"創建擴展性圖表時發生錯誤: {e}")
            return None
    
    def _create_dashboard(self, df: pd.DataFrame, output_dir: Path) -> Optional[str]:
        """創建綜合儀表板"""
        try:
            fig = plt.figure(figsize=(20, 12))
            gs = GridSpec(3, 3, figure=fig)
            
            # 主要性能指標概覽
            ax1 = fig.add_subplot(gs[0, :])
            grouped = df.groupby('robot_count').agg({
                'completion_rate': 'mean',
                'avg_wait_time': 'mean',
                'throughput': 'mean'
            })
            
            robot_counts = grouped.index
            
            # 多軸圖表
            ax1_twin1 = ax1.twinx()
            ax1_twin2 = ax1.twinx()
            ax1_twin2.spines['right'].set_position(('outward', 60))
            
            p1 = ax1.plot(robot_counts, grouped['completion_rate'], 'bo-', label='完成率')
            p2 = ax1_twin1.plot(robot_counts, grouped['avg_wait_time'], 'ro-', label='平均等待時間')
            p3 = ax1_twin2.plot(robot_counts, grouped['throughput'], 'go-', label='吞吐量')
            
            ax1.set_xlabel('機器人數量')
            ax1.set_ylabel('完成率', color='b')
            ax1_twin1.set_ylabel('平均等待時間', color='r')
            ax1_twin2.set_ylabel('吞吐量', color='g')
            ax1.set_title('RMFS 系統容量測試 - 主要性能指標 (所有數據為平均值)', fontsize=16, fontweight='bold', pad=20)
            
            # 最佳性能點標註
            best_perf = self.analysis_results.get('best_performance', {})
            if 'highest_completion_rate' in best_perf:
                best_robot_count = best_perf['highest_completion_rate']['robot_count']
                ax1.annotate(f'最佳完成率\n{best_robot_count} 機器人', 
                           xy=(best_robot_count, best_perf['highest_completion_rate']['completion_rate']),
                           xytext=(best_robot_count + 2, 0.8), fontsize=10,
                           arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7))
            
            # 其他子圖...
            # 效率分析
            ax2 = fig.add_subplot(gs[1, 0])
            df_eff = df.copy()
            df_eff['orders_per_robot'] = df_eff['completed_orders'] / df_eff['robot_count']
            eff_grouped = df_eff.groupby('robot_count')['orders_per_robot'].mean()
            
            ax2.bar(eff_grouped.index, eff_grouped.values, color='skyblue', alpha=0.7)
            ax2.set_title('機器人效率')
            ax2.set_xlabel('機器人數量')
            ax2.set_ylabel('每機器人訂單數')
            
            # 能源效率
            ax3 = fig.add_subplot(gs[1, 1])
            energy_grouped = df.groupby('robot_count')['energy_per_order'].mean()
            ax3.plot(energy_grouped.index, energy_grouped.values, 'ro-')
            ax3.set_title('能源效率')
            ax3.set_xlabel('機器人數量')
            ax3.set_ylabel('每訂單能源消耗')
            
            # 擴展性
            ax4 = fig.add_subplot(gs[1, 2])
            scalability = self.analysis_results.get('scalability', {})
            linear_data = scalability.get('linear_scalability', [])
            
            if linear_data:
                counts = [item['robot_count'] for item in linear_data]
                ratios = [item['scalability_ratio'] for item in linear_data]
                ax4.bar(counts, ratios, color='lightgreen', alpha=0.7)
                ax4.axhline(y=1.0, color='red', linestyle='--', alpha=0.7)
                ax4.set_title('擴展性')
                ax4.set_xlabel('機器人數量')
                ax4.set_ylabel('擴展性比率')
            
            # 摘要文字
            ax5 = fig.add_subplot(gs[2, :])
            ax5.axis('off')
            
            summary_text = self._generate_summary_text()
            ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes, fontsize=12,
                    verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.5))
            
            plt.tight_layout()
            
            chart_file = output_dir / 'dashboard.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            self.logger.error(f"創建儀表板時發生錯誤: {e}")
            return None

    def _create_cleaning_comparison_chart(self, output_dir: Path) -> Optional[str]:
        """創建資料清洗前後比較圖"""
        try:
            if not self.cleaning_stats or 'df_original' not in self.processed_data:
                self.logger.info("沒有資料清洗統計，跳過清洗比較圖")
                return None
            
            # 設定中文字體
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('資料清洗分析報告', fontsize=16, fontweight='bold')
            
            # 準備數據
            df_original = self.processed_data['df_original']
            df_cleaned = self.processed_data['df']
            
            # 1. 各機器人數量的數據清洗情況
            robot_counts = [k for k in self.cleaning_stats.keys() if k != 'overall']
            robot_counts = sorted(robot_counts)
            
            original_counts = []
            cleaned_counts = []
            removed_counts = []
            
            for rc in robot_counts:
                if rc in self.cleaning_stats:
                    stats = self.cleaning_stats[rc]
                    original_counts.append(stats['original_count'])
                    cleaned_counts.append(stats['cleaned_count'])
                    removed_counts.append(stats['removed_count'])
            
            if robot_counts:
                x = np.arange(len(robot_counts))
                width = 0.35
                
                bars1 = ax1.bar(x - width/2, original_counts, width, label='原始數據', alpha=0.8, color='lightblue')
                bars2 = ax1.bar(x + width/2, cleaned_counts, width, label='清洗後數據', alpha=0.8, color='lightgreen')
                
                ax1.set_xlabel('機器人數量', fontsize=12)
                ax1.set_ylabel('數據筆數', fontsize=12)
                ax1.set_title('資料清洗前後數據量比較', fontsize=14)
                ax1.set_xticks(x)
                ax1.set_xticklabels(robot_counts)
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # 添加數值標籤
                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom')
                for bar in bars2:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom')
            else:
                ax1.text(0.5, 0.5, '無數據', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('資料清洗前後數據量比較', fontsize=14)
            
            # 2. 完成訂單數分布比較（箱形圖）
            data_for_box = []
            labels_for_box = []
            
            for rc in robot_counts:
                # 原始數據
                orig_data = df_original[df_original['robot_count'] == rc]['completed_orders']
                if len(orig_data) > 0:
                    data_for_box.append(orig_data)
                    labels_for_box.append(f'{rc}\n(原始)')
                
                # 清洗後數據
                clean_data = df_cleaned[df_cleaned['robot_count'] == rc]['completed_orders']
                if len(clean_data) > 0:
                    data_for_box.append(clean_data)
                    labels_for_box.append(f'{rc}\n(清洗後)')
            
            if data_for_box:
                ax2.boxplot(data_for_box, labels=labels_for_box)
                ax2.set_xlabel('機器人數量', fontsize=12)
                ax2.set_ylabel('完成訂單數', fontsize=12)
                ax2.set_title('完成訂單數分布比較', fontsize=14)
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, '無數據', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('完成訂單數分布比較', fontsize=14)
            
            # 3. 異常值展示
            if self.outliers_removed:
                outliers_df = pd.DataFrame(self.outliers_removed)
                outliers_by_robot = outliers_df.groupby('robot_count').size()
                
                ax3.bar(outliers_by_robot.index, outliers_by_robot.values, color='red', alpha=0.7)
                ax3.set_xlabel('機器人數量', fontsize=12)
                ax3.set_ylabel('異常數據筆數', fontsize=12)
                ax3.set_title('各機器人數量的異常數據分布', fontsize=14)
                ax3.grid(True, alpha=0.3)
                
                # 添加數值標籤
                for i, (rc, count) in enumerate(outliers_by_robot.items()):
                    ax3.text(rc, count + 0.1, str(count), ha='center', va='bottom')
                
                # 設定 x 軸範圍，確保標籤顯示正確
                ax3.set_xticks(list(outliers_by_robot.index))
            else:
                ax3.text(0.5, 0.5, '無異常數據', ha='center', va='center', transform=ax3.transAxes, fontsize=14)
                ax3.set_title('各機器人數量的異常數據分布', fontsize=14)
                ax3.set_xlabel('機器人數量', fontsize=12)
                ax3.set_ylabel('異常數據筆數', fontsize=12)
            
            # 4. 清洗效果摘要
            ax4.axis('off')
            
            summary_text = "資料清洗摘要\n" + "=" * 40 + "\n"
            
            if 'overall' in self.cleaning_stats:
                overall = self.cleaning_stats['overall']
                summary_text += f"總數據量: {overall['original_count']} 筆\n"
                summary_text += f"清洗後: {overall['cleaned_count']} 筆\n"
                summary_text += f"移除: {overall['removed_count']} 筆 ({overall['removal_rate']:.1f}%)\n\n"
            
            summary_text += "異常數據範例:\n"
            if self.outliers_removed:
                for i, outlier in enumerate(self.outliers_removed[:5]):  # 顯示前5筆
                    summary_text += f"• 機器人{outlier['robot_count']}: "
                    summary_text += f"完成{outlier['completed_orders']}/{outlier['total_orders']}訂單\n"
                
                if len(self.outliers_removed) > 5:
                    summary_text += f"  ... 還有 {len(self.outliers_removed) - 5} 筆異常數據"
            else:
                summary_text += "無異常數據被移除"
            
            ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=11,
                    verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
            
            plt.tight_layout()
            
            chart_file = output_dir / 'data_cleaning_comparison.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            self.logger.error(f"創建資料清洗比較圖時發生錯誤: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _generate_summary_text(self) -> str:
        """生成摘要文字"""
        best_perf = self.analysis_results.get('best_performance', {})
        scalability = self.analysis_results.get('scalability', {})
        
        summary_parts = [
            "RMFS 容量測試分析摘要",
            "=" * 50
        ]
        
        if 'highest_completion_rate' in best_perf:
            cr_data = best_perf['highest_completion_rate']
            summary_parts.append(f"最佳完成率: {cr_data['robot_count']} 機器人 ({cr_data['completion_rate']:.1%})")
        
        if 'highest_efficiency' in best_perf:
            eff_data = best_perf['highest_efficiency']
            summary_parts.append(f"最高效率: {eff_data['robot_count']} 機器人 ({eff_data['orders_per_robot']:.1f} 訂單/機器人)")
        
        if 'best_energy_efficiency' in best_perf:
            energy_data = best_perf['best_energy_efficiency']
            summary_parts.append(f"最佳能源效率: {energy_data['robot_count']} 機器人 ({energy_data['energy_per_order']:.1f} 能源/訂單)")
        
        if scalability.get('capacity_saturation'):
            summary_parts.append(f"容量飽和點: {scalability.get('saturation_point', 'N/A')} 機器人")
        
        return "\n".join(summary_parts)
    
    def set_cleaning_enabled(self, enabled: bool):
        """
        設定是否啟用資料清洗
        
        Args:
            enabled: 是否啟用資料清洗
        """
        self.enable_cleaning = enabled
        self.logger.info(f"資料清洗功能已{'啟用' if enabled else '停用'}")

    def generate_analysis_report(self) -> str:
        """
        生成完整的分析報告
        
        Returns:
            報告檔案路徑
        """
        try:
            # 載入和處理數據
            if not self.load_test_data():
                raise Exception("無法載入測試數據")
            
            if not self.process_data():
                raise Exception("無法處理測試數據")
            
            # 生成圖表
            chart_files = self.generate_charts()
            
            # 生成文字報告
            report_file = self._generate_text_report(chart_files)
            
            self.logger.info(f"分析報告已生成: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"生成分析報告時發生錯誤: {e}")
            return ""
    
    def _generate_text_report(self, chart_files: List[str]) -> str:
        """生成文字報告"""
        report_file = self.results_dir / f'capacity_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# RMFS 系統容量壓力測試分析報告\n\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 測試概述
            f.write("## 測試概述\n\n")
            total_tests = len(self.raw_data)
            f.write(f"- 測試會話數量: {total_tests}\n")
            
            if 'df' in self.processed_data:
                df = self.processed_data['df']
                robot_counts = sorted(df['robot_count'].unique())
                f.write(f"- 測試機器人數量: {robot_counts}\n")
                f.write(f"- 總測試數量: {len(df)}\n")
                
                # 加入資料清洗統計
                if self.enable_cleaning and 'overall' in self.cleaning_stats:
                    overall = self.cleaning_stats['overall']
                    f.write(f"\n### 資料清洗統計\n")
                    f.write(f"- 原始數據: {overall['original_count']} 筆\n")
                    f.write(f"- 清洗後數據: {overall['cleaned_count']} 筆\n")
                    f.write(f"- 移除異常數據: {overall['removed_count']} 筆 ({overall['removal_rate']:.1f}%)\n")
                f.write("\n")
            
            # 關鍵發現
            f.write("## 關鍵發現\n\n")
            
            best_perf = self.analysis_results.get('best_performance', {})
            if best_perf:
                f.write("### 最佳性能配置\n\n")
                
                if 'highest_completion_rate' in best_perf:
                    cr_data = best_perf['highest_completion_rate']
                    f.write(f"- **最高完成率**: {cr_data['robot_count']} 機器人 ({cr_data['completion_rate']:.1%})\n")
                
                if 'highest_efficiency' in best_perf:
                    eff_data = best_perf['highest_efficiency']
                    f.write(f"- **最高效率**: {eff_data['robot_count']} 機器人 ({eff_data['orders_per_robot']:.1f} 訂單/機器人)\n")
                
                if 'best_energy_efficiency' in best_perf:
                    energy_data = best_perf['best_energy_efficiency']
                    f.write(f"- **最佳能源效率**: {energy_data['robot_count']} 機器人 ({energy_data['energy_per_order']:.1f} 能源/訂單)\n\n")
            
            # 擴展性分析
            scalability = self.analysis_results.get('scalability', {})
            if scalability:
                f.write("### 擴展性分析\n\n")
                
                if scalability.get('capacity_saturation'):
                    f.write(f"- **容量飽和**: 在 {scalability.get('saturation_point')} 機器人時出現容量飽和\n")
                
                linear_data = scalability.get('linear_scalability', [])
                if linear_data:
                    avg_scalability = np.mean([item['scalability_ratio'] for item in linear_data])
                    f.write(f"- **平均擴展性比率**: {avg_scalability:.2f}\n")
                    
                    if avg_scalability > 0.8:
                        f.write("- **擴展性評估**: 良好，系統能有效利用額外的機器人\n")
                    elif avg_scalability > 0.6:
                        f.write("- **擴展性評估**: 中等，存在一定的擴展性瓶頸\n")
                    else:
                        f.write("- **擴展性評估**: 較差，系統存在嚴重的擴展性問題\n")
                
                f.write("\n")
            
            # 詳細統計
            if 'by_robot_count' in self.analysis_results:
                f.write("## 詳細統計\n\n")
                grouped = self.analysis_results['by_robot_count']
                
                # 加入異常數據摘要
                if self.outliers_removed:
                    f.write("### 異常數據摘要\n\n")
                    outliers_df = pd.DataFrame(self.outliers_removed)
                    outliers_by_robot = outliers_df.groupby('robot_count').size()
                    
                    f.write("| 機器人數量 | 異常數據筆數 | 異常原因 |\n")
                    f.write("|-----------|------------|----------|\n")
                    for rc, count in outliers_by_robot.items():
                        reasons = outliers_df[outliers_df['robot_count'] == rc]['reason'].iloc[0]
                        f.write(f"| {rc} | {count} | {reasons} |\n")
                    f.write("\n")
                
                f.write("### 清洗後統計數據\n\n")
                f.write("| 機器人數量 | 平均完成率 | 平均等待時間 | 平均能源消耗 | 平均能源/訂單 |\n")
                f.write("|-----------|------------|-------------|-------------|---------------|\n")
                
                for robot_count in grouped.index:
                    completion_rate = grouped.loc[robot_count]['completion_rate']['mean']
                    wait_time = grouped.loc[robot_count]['avg_wait_time']['mean']
                    total_energy = grouped.loc[robot_count]['total_energy']['mean']
                    energy_per_order = grouped.loc[robot_count]['energy_per_order']['mean']
                    
                    f.write(f"| {robot_count} | {completion_rate:.1%} | {wait_time:.2f} | {total_energy:.0f} | {energy_per_order:.2f} |\n")
                
                f.write("\n")
            
            # 圖表
            if chart_files:
                f.write("## 分析圖表\n\n")
                for chart_file in chart_files:
                    if chart_file:
                        chart_name = Path(chart_file).stem
                        f.write(f"- [{chart_name}]({Path(chart_file).name})\n")
                f.write("\n")
            
            # 建議
            f.write("## 建議\n\n")
            
            if best_perf:
                if 'highest_completion_rate' in best_perf:
                    cr_count = best_perf['highest_completion_rate']['robot_count']
                    f.write(f"1. **推薦機器人數量**: {cr_count} 機器人可達到最高完成率\n")
                
                if 'highest_efficiency' in best_perf:
                    eff_count = best_perf['highest_efficiency']['robot_count']
                    f.write(f"2. **效率最佳配置**: {eff_count} 機器人可達到最佳單機器人效率\n")
                
                if scalability.get('capacity_saturation'):
                    sat_point = scalability.get('saturation_point')
                    f.write(f"3. **容量規劃**: 建議不超過 {sat_point} 機器人，避免資源浪費\n")
            
            f.write("\n---\n\n")
            f.write("*本報告由 RMFS 容量分析器自動生成*\n")
        
        return str(report_file)


def main():
    """主函數，用於命令列執行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RMFS 容量分析器')
    parser.add_argument('results_dir', help='測試結果目錄路徑')
    parser.add_argument('--charts-only', action='store_true', help='只生成圖表，不生成報告')
    parser.add_argument('--report-only', action='store_true', help='只生成報告，不生成圖表')
    
    args = parser.parse_args()
    
    try:
        analyzer = CapacityAnalyzer(Path(args.results_dir))
        
        if args.charts_only:
            analyzer.load_test_data()
            analyzer.process_data()
            chart_files = analyzer.generate_charts()
            print(f"已生成 {len(chart_files)} 個圖表")
            for chart_file in chart_files:
                if chart_file:
                    print(f"- {chart_file}")
        elif args.report_only:
            report_file = analyzer.generate_analysis_report()
            print(f"分析報告已生成: {report_file}")
        else:
            report_file = analyzer.generate_analysis_report()
            print(f"完整分析報告已生成: {report_file}")
    
    except Exception as e:
        print(f"分析失敗: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()