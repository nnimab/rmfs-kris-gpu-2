#!/usr/bin/env python3
"""
修復 matplotlib 中文字體問題
在沒有中文字體的環境中使用英文替代
"""

import matplotlib.pyplot as plt
import matplotlib

def setup_matplotlib_font():
    """設置 matplotlib 使用支援的字體"""
    # 嘗試不同的字體選項
    font_options = [
        'DejaVu Sans',
        'Liberation Sans',
        'Arial',
        'Helvetica',
        'sans-serif'
    ]
    
    # 找到第一個可用的字體
    available_fonts = set([f.name for f in matplotlib.font_manager.fontManager.ttflist])
    
    for font in font_options:
        if font in available_fonts:
            matplotlib.rcParams['font.sans-serif'] = [font]
            print(f"使用字體: {font}")
            break
    
    matplotlib.rcParams['axes.unicode_minus'] = False
    
    # 如果在無中文字體環境，使用英文標籤
    return check_chinese_font_support()

def check_chinese_font_support():
    """檢查是否支援中文字體"""
    try:
        fig, ax = plt.subplots(figsize=(1, 1))
        ax.text(0.5, 0.5, '測試', fontsize=12)
        plt.close(fig)
        return True
    except:
        return False

def get_chart_labels(chinese_support=True):
    """根據字體支援情況返回圖表標籤"""
    if chinese_support:
        return {
            'title': '控制器性能評估比較',
            'completion_rate': '訂單完成率比較',
            'wait_time': '平均等待時間比較',
            'energy': '能源效率比較',
            'utilization': '機器人利用率比較',
            'completion_rate_y': '完成率 (%)',
            'wait_time_y': '等待時間 (ticks)',
            'energy_y': '每訂單能源消耗',
            'utilization_y': '利用率 (%)'
        }
    else:
        return {
            'title': 'Controller Performance Comparison',
            'completion_rate': 'Order Completion Rate',
            'wait_time': 'Average Wait Time',
            'energy': 'Energy Efficiency',
            'utilization': 'Robot Utilization',
            'completion_rate_y': 'Completion Rate (%)',
            'wait_time_y': 'Wait Time (ticks)',
            'energy_y': 'Energy per Order',
            'utilization_y': 'Utilization (%)'
        }

if __name__ == "__main__":
    # 測試字體設置
    chinese_support = setup_matplotlib_font()
    print(f"中文字體支援: {chinese_support}")
    
    labels = get_chart_labels(chinese_support)
    print("圖表標籤:")
    for key, value in labels.items():
        print(f"  {key}: {value}")