#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終比較實驗分析器

功能：
- 掃描 `test/final_exp_results/<controller>/<SIMULATION_ID>/` 內的 evaluation 與時間序列輸出
- 彙整各控制器的核心 KPI（完成訂單、完成率、平均等待、利用率、能源、訊號切換等）
- 產製比較圖表（每控制器的箱型圖/條形圖）
- 產製時間序列比較圖（可選移動平均平滑）
- 進行基本統計比較（均值、標準差、t 檢定 p 值）

輸出：
- `test/final_exp_results/summary/` 內的圖表與彙整 CSV
"""

import argparse
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re


def find_runs(root: Path):
    """掃描三控制器結果目錄，回傳每個控制器下所有 run 的路徑清單。"""
    controllers = []
    for label in ["nerl_global", "time_based", "no_controller"]:
        ctrl_dir = root / label
        if not ctrl_dir.exists():
            continue
        sim_dirs = []
        for child in ctrl_dir.iterdir():
            if child.is_dir():
                # run 產出在 <label>/<SIMULATION_ID>/
                sim_dirs.append(child)
        controllers.append((label, sim_dirs))
    return controllers


def load_one_run(sim_dir: Path):
    """讀取單次 run 的 evaluation 結果與時間序列。"""
    eval_json = sim_dir / "evaluation_results.json"
    # 舊版 evaluate 直接落在 sim_dir；新版時間序列在 sim_dir/<SIMULATION_ID>/time_series_*.csv
    # 嘗試從 sim_dir 名稱抓 SIMULATION_ID
    sim_id = sim_dir.name
    ts_dir = sim_dir / sim_id
    time_series_csv = None
    if ts_dir.exists():
        # 嘗試找到第一個 time_series 檔
        candidates = list(ts_dir.glob("time_series_*.csv"))
        if candidates:
            time_series_csv = candidates[0]
    else:
        # 後備：舊格式（不建子資料夾）
        candidates = list(sim_dir.glob("time_series_*.csv"))
        if candidates:
            time_series_csv = candidates[0]

    eval_df = None
    if eval_json.exists():
        try:
            with open(eval_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            eval_df = pd.DataFrame(data.get('results', []))
        except Exception:
            eval_df = None

    ts_df = None
    if time_series_csv and time_series_csv.exists():
        try:
            ts_df = pd.read_csv(time_series_csv)
        except Exception:
            ts_df = None

    return eval_df, ts_df


def moving_average(series: pd.Series, window: int):
    if window and window > 1:
        return series.rolling(window=window, min_periods=1, center=False).mean()
    return series


def build_comparison(root: Path, smoothing: int = 0):
    controllers = find_runs(root)
    if not controllers:
        return "找不到任何控制器結果。"

    summary_dir = root / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    # 收集所有 evaluation 結果
    eval_rows = []
    ts_rows = []

    for label, sim_dirs in controllers:
        for sim_dir in sim_dirs:
            eval_df, ts_df = load_one_run(sim_dir)
            if eval_df is not None and not eval_df.empty:
                # 每個 run 只會有一筆結果（因 evaluate.py num_runs=1）
                row = eval_df.iloc[0].to_dict()
                row['controller_label'] = label
                row['sim_id'] = sim_dir.name
                eval_rows.append(row)
            if ts_df is not None and not ts_df.empty:
                df = ts_df.copy()
                df['controller_label'] = label
                df['sim_id'] = sim_dir.name
                # 平滑（時間序列）
                for col in [
                    'completed_orders', 'total_orders', 'unfinished_orders',
                    'total_energy', 'signal_switch_count', 'avg_traffic_rate',
                    'robot_utilization'
                ]:
                    if col in df.columns:
                        df[col] = moving_average(df[col], smoothing)
                ts_rows.append(df)

    if not eval_rows:
        return "找不到 evaluation_results.json 的資料。"

    eval_all = pd.DataFrame(eval_rows)
    eval_csv = summary_dir / 'final_comparison_summary.csv'
    eval_all.to_csv(eval_csv, index=False, encoding='utf-8')

    # 指標箱型圖/條形圖
    kpis = [
        ('completion_rate', 'Completion Rate'),
        ('avg_wait_time', 'Average Wait Time (ticks)'),
        ('robot_utilization', 'Robot Utilization'),
        ('energy_per_order', 'Energy per Order'),
        ('signal_switch_count', 'Signal Switch Count'),
        ('avg_traffic_rate', 'Average Traffic Rate')
    ]
    for col, label_en in kpis:
        if col in eval_all.columns:
            # 轉數值避免文字污染
            try:
                eval_all[col] = pd.to_numeric(eval_all[col], errors='coerce')
            except Exception:
                pass
            plt.figure(figsize=(7,5))
            eval_all.boxplot(column=col, by='controller_label')
            plt.title(f'{label_en} (Boxplot)')
            plt.suptitle('')
            plt.xlabel('Controller')
            plt.ylabel(label_en)
            out = summary_dir / f'box_{col}.png'
            plt.tight_layout()
            plt.savefig(out, dpi=150)
            plt.close()

            # 平均條形圖
            plt.figure(figsize=(7,5))
            # 為避免非數值值造成 groupby.mean 失敗，先 dropna
            means = eval_all[['controller_label', col]].dropna().groupby('controller_label')[col].mean()
            # 重新排序控制器顯示順序
            means = means.reindex(['nerl_global','time_based','no_controller'])
            means.plot(kind='bar', rot=0)
            plt.title(f'{label_en} (Average)')
            plt.xlabel('Controller')
            plt.ylabel(label_en)
            out = summary_dir / f'bar_{col}.png'
            plt.tight_layout()
            plt.savefig(out, dpi=150)
            plt.close()

    # 時間序列比較圖（若有）
    if ts_rows:
        ts_all = pd.concat(ts_rows, ignore_index=True)
        # 數值轉換（避免 CSV 讀取為字串）
        if 'python_tick' in ts_all.columns:
            try:
                ts_all['python_tick'] = pd.to_numeric(ts_all['python_tick'], errors='coerce')
            except Exception:
                pass
        # 以 python_tick 為 X，分控制器畫幾個常见欄位
        ts_kpis = [
            ('completed_orders', 'Completed Orders'),
            ('unfinished_orders', 'Unfinished Orders'),
            ('total_energy', 'Cumulative Energy'),
            ('signal_switch_count', 'Signal Switch Count'),
            ('avg_traffic_rate', 'Average Traffic Rate'),
            ('robot_utilization', 'Robot Utilization')
        ]
        for col, label_en in ts_kpis:
            if col not in ts_all.columns:
                continue
            # 轉數值避免非數值導致 groupby.mean 失敗
            try:
                ts_all[col] = pd.to_numeric(ts_all[col], errors='coerce')
            except Exception:
                pass
            plt.figure(figsize=(8,5))
            for label in ['nerl_global','time_based','no_controller']:
                sub = ts_all[ts_all['controller_label']==label]
                if sub.empty:
                    continue
                # 聚合同一控制器的多個 run：先 groupby tick 求平均
                # 保險處理：只取數值且去除 NaN
                sub_local = sub[['python_tick', col]].dropna()
                grp = sub_local.groupby('python_tick')[col].mean()
                grp.plot(label=label)
            plt.legend()
            plt.title(f'Time Series: {label_en}')
            plt.xlabel('python_tick')
            plt.ylabel(label_en)
            out = summary_dir / f'ts_{col}.png'
            plt.tight_layout()
            plt.savefig(out, dpi=150)
            plt.close()

    # 簡單統計表（平均、標準差、樣本數）—僅針對數值型 KPI 欄位
    metric_cols = [c for c, _ in kpis if c in eval_all.columns]
    # 嘗試將 KPI 欄位強制轉數值（保險）
    for c in metric_cols:
        try:
            eval_all[c] = pd.to_numeric(eval_all[c], errors='coerce')
        except Exception:
            pass
    if metric_cols:
        stats = eval_all.groupby('controller_label')[metric_cols].agg(['mean','std','count'])
        stats.to_csv(summary_dir / 'kpi_stats.csv', encoding='utf-8')

    # 可選的簡易 t 檢定（成對比較）
    try:
        from scipy.stats import ttest_ind
        comp_pairs = [('nerl_global','time_based'), ('nerl_global','no_controller'), ('time_based','no_controller')]
        rows = []
        for metric, _ in kpis:
            if metric not in eval_all.columns:
                continue
            for a,b in comp_pairs:
                va = eval_all.loc[eval_all['controller_label']==a, metric].dropna()
                vb = eval_all.loc[eval_all['controller_label']==b, metric].dropna()
                if len(va)>1 and len(vb)>1:
                    t, p = ttest_ind(va, vb, equal_var=False)
                    rows.append({'metric':metric, 'A':a, 'B':b, 't':t, 'p_value':p, 'nA':len(va), 'nB':len(vb)})
        if rows:
            pd.DataFrame(rows).to_csv(summary_dir / 't_tests.csv', index=False, encoding='utf-8')
    except Exception:
        pass

    return f"輸出：{summary_dir}（包含 summary CSV 與各項圖表）"


def main():
    parser = argparse.ArgumentParser(description='最終比較實驗分析器')
    parser.add_argument('--root', type=str, required=True, help='final_exp_results 根目錄路徑')
    parser.add_argument('--smoothing', type=int, default=0, help='時間序列移動平均窗口（0=不平滑）')
    args = parser.parse_args()

    root = Path(args.root)
    msg = build_comparison(root, smoothing=args.smoothing)
    print(msg)

if __name__ == '__main__':
    main()


