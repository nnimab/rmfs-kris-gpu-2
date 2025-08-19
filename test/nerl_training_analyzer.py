#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新 NERL 訓練分析器（重寫版）

目的：
- 僅依據每代資料夾 genXXX 內的 fitness_scores.json（不再依賴 training.log）。
- 匯整每代「最佳個體」的各項 KPI 與適應度，繪製世代走勢圖。
- 匯出統計（Early vs Late、與世代/適應度的 Spearman 相關）。

輸入：models/training_runs/<run_dir>/
  - genXXX/fitness_scores.json（至少包含：generation、best_fitness、all_fitness、best_individual_metrics）

輸出：<run_dir>/analysis/
  - per_generation_metrics.csv（每代彙整：best_fitness、mean_fitness、std_fitness、各 KPI）
  - per_generation_fitness_long.csv（若提供 all_fitness：長表 generation, fitness）
  - fitness_over_generations.png（最佳/平均適應度走勢）
  - metric_<KPI>.png（每個 KPI 的世代走勢）
  - metrics_over_generations_overview.png（多面板 KPI 總覽，最多 12 個）
  - early_vs_late_best_fitness.csv（首 25% vs 末 25% 的 best_fitness 對比）
  - trend_spearman_vs_generation.csv（best/mean 與世代的 Spearman 相關）
  - spearman_best_fitness_vs_metrics.csv（best_fitness 與各 KPI 的 Spearman 相關）
  - training_analysis_report.md（Markdown 摘要）
"""

from pathlib import Path
import json
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def scan_gen_dirs(run_dir: Path):
    gens = []
    for child in run_dir.iterdir():
        if child.is_dir():
            m = re.fullmatch(r"gen(\d{3})", child.name)
            if m:
                gens.append((int(m.group(1)), child))
    gens.sort(key=lambda x: x[0])
    return gens


def compute_trend_spearman(series_x: pd.Series, series_y: pd.Series) -> dict:
    try:
        v = pd.DataFrame({'x': series_x, 'y': series_y}).dropna()
        if len(v) < 3:
            return {'rho': np.nan, 'n': int(len(v))}
        rho = v['x'].corr(v['y'], method='spearman')
        return {'rho': float(rho), 'n': int(len(v))}
    except Exception:
        return {'rho': np.nan, 'n': 0}


def analyze_run_dir(run_dir: Path):
    out_dir = run_dir / 'analysis'
    out_dir.mkdir(parents=True, exist_ok=True)

    gen_rows = []
    fit_long_rows = []
    for gen_num, gen_dir in scan_gen_dirs(run_dir):
        fs = gen_dir / 'fitness_scores.json'
        if not fs.exists():
            continue
        try:
            obj = json.loads(fs.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            continue

        generation = int(obj.get('generation', gen_num))
        all_fitness = obj.get('all_fitness') or []
        best_fitness = obj.get('best_fitness')
        if best_fitness is None:
            try:
                best_fitness = max([float(v) for v in all_fitness]) if all_fitness else np.nan
            except Exception:
                best_fitness = np.nan

        # 分布蒐集
        for v in all_fitness:
            try:
                fit_long_rows.append({'generation': generation, 'fitness': float(v)})
            except Exception:
                pass

        # 最佳個體 KPI（動態鍵）
        metrics = obj.get('best_individual_metrics') or {}
        # 統計量
        if all_fitness:
            arr = pd.to_numeric(pd.Series(all_fitness), errors='coerce')
            mean_fitness = float(arr.mean())
            std_fitness = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
        else:
            mean_fitness = np.nan
            std_fitness = np.nan

        row = {
            'generation': generation,
            'best_fitness': best_fitness,
            'mean_fitness': mean_fitness,
            'std_fitness': std_fitness,
        }
        for k, v in metrics.items():
            try:
                row[k] = float(v)
            except Exception:
                pass
        gen_rows.append(row)

    if not gen_rows:
        print(f"No generation data found under: {run_dir}")
        return

    gen_df = pd.DataFrame(gen_rows).sort_values('generation')
    fit_long = pd.DataFrame(fit_long_rows)

    # 儲存 CSV
    gen_df.to_csv(out_dir / 'per_generation_metrics.csv', index=False, encoding='utf-8')
    if not fit_long.empty:
        fit_long.sort_values(['generation']).to_csv(out_dir / 'per_generation_fitness_long.csv', index=False, encoding='utf-8')

    # 圖表：Fitness 走勢
    plt.figure(figsize=(9,5))
    plt.plot(gen_df['generation'], gen_df['best_fitness'], label='Best Fitness', marker='o')
    if 'mean_fitness' in gen_df.columns and not gen_df['mean_fitness'].isna().all():
        plt.plot(gen_df['generation'], gen_df['mean_fitness'], label='Mean Fitness', marker='s')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.title('Fitness over Generations')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / 'fitness_over_generations.png', dpi=150)
    plt.close()

    # 圖表：各 KPI 走勢（最佳個體）
    preferred_order = [
        'completed_orders','total_orders','completion_rate',
        'avg_order_processing_time','avg_wait_time','max_wait_time','total_wait_time',
        'robot_utilization','avg_traffic_rate','signal_switch_count',
        'total_energy_consumed','total_energy','energy_per_order',
        'total_stop_go_events','spillback_penalty_total','evaluation_ticks'
    ]
    available_metrics = [m for m in preferred_order if m in gen_df.columns]
    for c in gen_df.columns:
        if c not in ['generation','best_fitness','mean_fitness','std_fitness'] and c not in available_metrics:
            available_metrics.append(c)

    for m in available_metrics:
        try:
            if gen_df[m].dropna().empty:
                continue
            plt.figure(figsize=(8,4))
            plt.plot(gen_df['generation'], gen_df[m], marker='o')
            plt.xlabel('Generation')
            plt.ylabel(m)
            plt.title(f'{m} over Generations (best individual)')
            plt.tight_layout()
            safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", m)
            plt.savefig(out_dir / f'metric_{safe_name}.png', dpi=150)
            plt.close()
        except Exception:
            pass

    # 多面板總覽（最多 12 個指標）
    top_metrics = [m for m in preferred_order if m in available_metrics][:12]
    if top_metrics:
        cols = 3
        rows = int(np.ceil(len(top_metrics)/cols))
        plt.figure(figsize=(cols*5, rows*3.2))
        for i, m in enumerate(top_metrics, start=1):
            ax = plt.subplot(rows, cols, i)
            try:
                ax.plot(gen_df['generation'], gen_df[m], marker='o')
                ax.set_title(m)
                ax.set_xlabel('Gen')
            except Exception:
                ax.set_visible(False)
        plt.tight_layout()
        plt.savefig(out_dir / 'metrics_over_generations_overview.png', dpi=150)
        plt.close()

    # 統計：early vs late（以 best_fitness）
    early_late = pd.DataFrame()
    try:
        per_gen_best = gen_df[['generation','best_fitness']].dropna()
        if len(per_gen_best) >= 4:
            n = len(per_gen_best)
            k = max(1, n//4)
            early = per_gen_best.sort_values('generation').iloc[:k]['best_fitness'].values
            late = per_gen_best.sort_values('generation').iloc[-k:]['best_fitness'].values
            diff = float(np.mean(late) - np.mean(early))
            s1 = np.var(early, ddof=1); s2 = np.var(late, ddof=1)
            n1 = len(early); n2 = len(late)
            sp = np.sqrt(((n1-1)*s1 + (n2-1)*s2)/(n1+n2-2)) if (n1+n2-2)>0 else np.nan
            cohen_d = diff / sp if sp and sp>0 else np.nan
            early_late = pd.DataFrame([{
                'early_gens': int(n1), 'late_gens': int(n2),
                'early_mean': float(np.mean(early)), 'late_mean': float(np.mean(late)),
                'diff_late_minus_early': diff, 'cohen_d': cohen_d
            }])
    except Exception:
        pass
    if not early_late.empty:
        early_late.to_csv(out_dir / 'early_vs_late_best_fitness.csv', index=False, encoding='utf-8')

    # 統計：世代趨勢（Spearman，generation vs best/mean）
    trend_rows = []
    try:
        trend_rows.append({'metric':'best_fitness', **compute_trend_spearman(gen_df['generation'], gen_df['best_fitness'])})
        if 'mean_fitness' in gen_df.columns:
            trend_rows.append({'metric':'mean_fitness', **compute_trend_spearman(gen_df['generation'], gen_df['mean_fitness'])})
    except Exception:
        pass
    trend_df = pd.DataFrame(trend_rows)
    if not trend_df.empty:
        trend_df.to_csv(out_dir / 'trend_spearman_vs_generation.csv', index=False, encoding='utf-8')

    # 統計：best_fitness 與各 KPI 相關（Spearman）
    corr_rows = []
    for m in available_metrics:
        if m in ['generation','best_fitness','mean_fitness','std_fitness']:
            continue
        try:
            v = gen_df[['best_fitness', m]].dropna()
            if len(v) < 3:
                rho = np.nan; n = len(v)
            else:
                rho = v['best_fitness'].corr(v[m], method='spearman')
                n = len(v)
            corr_rows.append({'metric': m, 'spearman_rho': float(rho) if rho==rho else np.nan, 'n': int(n)})
        except Exception:
            pass
    corr_df = pd.DataFrame(corr_rows).sort_values('spearman_rho', ascending=False)
    if not corr_df.empty:
        corr_df.to_csv(out_dir / 'spearman_best_fitness_vs_metrics.csv', index=False, encoding='utf-8')

    # Markdown 摘要
    try:
        lines = [
            '# NERL 訓練分析報告',
            '',
            '## Fitness 概覽',
            f"- 代數範圍：{int(gen_df['generation'].min())} ~ {int(gen_df['generation'].max())}",
            f"- 最佳適應度（首/末代）：{gen_df.iloc[0]['best_fitness']:.4f} → {gen_df.iloc[-1]['best_fitness']:.4f}",
            f"- 平均適應度（若有）：{('%.4f'%gen_df['mean_fitness'].iloc[-1]) if 'mean_fitness' in gen_df.columns and not gen_df['mean_fitness'].isna().all() else 'N/A'}",
            ''
        ]
        if not trend_df.empty:
            lines += ['## 趨勢（Spearman 對世代）','']
            lines.append('| 指標 | rho | n |')
            lines.append('|---|---:|---:|')
            for _, r in trend_df.iterrows():
                lines.append(f"| {r['metric']} | {r.get('rho', np.nan):.3f} | {int(r.get('n', 0))} |")
            lines.append('')
        if not corr_df.empty:
            lines += ['## 與最佳適應度相關（Spearman）','']
            lines.append('| KPI | rho | n |')
            lines.append('|---|---:|---:|')
            for _, r in corr_df.iterrows():
                lines.append(f"| {r['metric']} | {r.get('spearman_rho', np.nan):.3f} | {int(r.get('n', 0))} |")
            lines.append('')
        if not early_late.empty:
            row = early_late.iloc[0].to_dict()
            lines += ['## Early vs Late（best_fitness）','']
            lines += [
                f"- Early mean: {row.get('early_mean', float('nan')):.4f}",
                f"- Late mean: {row.get('late_mean', float('nan')):.4f}",
                f"- Diff (late-early): {row.get('diff_late_minus_early', float('nan')):.4f}",
                f"- Cohen's d: {row.get('cohen_d', float('nan')):.3f}",
                ''
            ]
        (out_dir / 'training_analysis_report.md').write_text('\n'.join(lines), encoding='utf-8')
    except Exception:
        pass

    print(f"Outputs written to: {out_dir}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze NERL training run directory (genXXX/fitness_scores.json based)')
    parser.add_argument('--run_dir', type=str, required=True, help='Path to models/training_runs/<run_dir>')
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Run dir not found: {run_dir}")
        return

    analyze_run_dir(run_dir)


if __name__ == '__main__':
    main()
