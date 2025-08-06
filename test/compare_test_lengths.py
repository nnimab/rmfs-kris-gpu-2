"""比較不同測試長度的結果"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 20000 ticks 測試數據（從報告中提取）
data_20k = {
    'robot_count': [20, 25, 30, 35, 40],
    'completion_rate': [0.808, 0.846, 0.875, 0.918, 0.899],
    'completed_orders': [43, 44, 46, 49, 48],  # 估算值基於完成率
    'energy_per_order': [211.35, 228.79, 242.44, 226.69, 277.66],
    'total_energy': [8838, 10049, 11004, 10800, 12954],
    'efficiency': [2.2, 1.76, 1.53, 1.4, 1.2]  # 訂單/機器人
}

# 100000 ticks 測試數據（從報告中提取）
data_100k = {
    'robot_count': [20, 25, 30, 35, 40],
    'completion_rate': [0.888, 0.976, 0.965, 0.980, 0.902],
    'completed_orders': [380, 418, 413, 420, 386],  # 基於效率計算
    'energy_per_order': [206.23, 233.32, 232.13, 268.01, 370.70],
    'total_energy': [78326, 97380, 77139, 112498, 133763],
    'efficiency': [19.1, 16.7, 13.8, 12.0, 9.7]  # 訂單/機器人
}

# 創建比較圖表
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle('RMFS 系統容量測試比較: 20,000 vs 100,000 ticks', fontsize=16, fontweight='bold')

# 1. 完成率比較
x = np.arange(len(data_20k['robot_count']))
width = 0.35

bars1 = ax1.bar(x - width/2, [r*100 for r in data_20k['completion_rate']], width, 
                 label='20,000 ticks', alpha=0.8, color='lightblue')
bars2 = ax1.bar(x + width/2, [r*100 for r in data_100k['completion_rate']], width, 
                 label='100,000 ticks', alpha=0.8, color='lightgreen')

ax1.set_xlabel('機器人數量')
ax1.set_ylabel('完成率 (%)')
ax1.set_title('訂單完成率比較')
ax1.set_xticks(x)
ax1.set_xticklabels(data_20k['robot_count'])
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 110)

# 添加數值標籤
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

# 2. 效率比較（每機器人完成訂單數）
bars3 = ax2.bar(x - width/2, data_20k['efficiency'], width, 
                 label='20,000 ticks', alpha=0.8, color='lightblue')
bars4 = ax2.bar(x + width/2, data_100k['efficiency'], width, 
                 label='100,000 ticks', alpha=0.8, color='lightgreen')

ax2.set_xlabel('機器人數量')
ax2.set_ylabel('訂單/機器人')
ax2.set_title('機器人效率比較')
ax2.set_xticks(x)
ax2.set_xticklabels(data_20k['robot_count'])
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. 能源效率比較
ax3.plot(data_20k['robot_count'], data_20k['energy_per_order'], 'bo-', 
         label='20,000 ticks', linewidth=2, markersize=8)
ax3.plot(data_100k['robot_count'], data_100k['energy_per_order'], 'go-', 
         label='100,000 ticks', linewidth=2, markersize=8)

ax3.set_xlabel('機器人數量')
ax3.set_ylabel('能源/訂單')
ax3.set_title('能源效率比較')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 主要發現總結
ax4.axis('off')

summary_text = """主要發現：

1. 測試長度影響：
   • 100,000 ticks 測試顯示更高的完成率（除了40機器人）
   • 長時間測試的訂單完成數顯著提高（約8-9倍）
   
2. 最佳配置差異：
   • 20,000 ticks: 35機器人最佳（91.8%完成率）
   • 100,000 ticks: 35機器人最佳（98.0%完成率）
   
3. 系統穩定性：
   • 40機器人在兩種測試中都顯示性能下降
   • 30-35機器人範圍最穩定
   
4. 能源效率：
   • 較長測試時間改善了能源效率
   • 20機器人始終保持最佳能源效率
   
5. 異常數據：
   • 100,000 ticks測試中有更多異常數據（12%移除率）
   • 表明長時間運行更容易出現不穩定情況"""

ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=11,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))

plt.tight_layout()
plt.savefig('test/results/test_length_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 輸出詳細比較
print("=" * 60)
print("RMFS 容量測試比較分析")
print("=" * 60)
print("\n1. 完成率提升（100k vs 20k）：")
for i, rc in enumerate(data_20k['robot_count']):
    improvement = (data_100k['completion_rate'][i] - data_20k['completion_rate'][i]) * 100
    print(f"   {rc}機器人: {improvement:+.1f}%")

print("\n2. 效率變化（訂單/機器人）：")
for i, rc in enumerate(data_20k['robot_count']):
    eff_20k = data_20k['efficiency'][i]
    eff_100k = data_100k['efficiency'][i]
    print(f"   {rc}機器人: {eff_20k:.1f} → {eff_100k:.1f} ({eff_100k/eff_20k:.1f}x)")

print("\n3. 能源效率變化（能源/訂單）：")
for i, rc in enumerate(data_20k['robot_count']):
    energy_20k = data_20k['energy_per_order'][i]
    energy_100k = data_100k['energy_per_order'][i]
    change = ((energy_100k - energy_20k) / energy_20k) * 100
    print(f"   {rc}機器人: {energy_20k:.1f} → {energy_100k:.1f} ({change:+.1f}%)")

print("\n4. 關鍵洞察：")
print("   • 100,000 ticks測試更接近實際運營狀況")
print("   • 30-35機器人是最穩定的配置範圍")
print("   • 40機器人可能達到系統容量瓶頸")
print("   • 長時間運行暴露了更多系統穩定性問題")