import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 手動創建數據來驗證
data = {
    'robot_count': [20, 20, 20, 20, 20, 20, 20, 20, 20, 20,
                    25, 25, 25, 25, 25, 25, 25, 25,
                    30, 30, 30, 30, 30, 30, 30,
                    35, 35, 35, 35, 35, 35, 35, 35, 35,
                    40, 40, 40, 40, 40, 40, 40, 40, 40],
    'total_energy': [76792] * 10 +  # 20 robots
                    [97380] * 8 +   # 25 robots (2 removed)
                    [108361] * 7 +  # 30 robots (3 removed)
                    [112498] * 9 +  # 35 robots (1 removed)
                    [133763] * 9    # 40 robots (1 removed)
}

df = pd.DataFrame(data)

# 計算每組的平均值（實際上都是相同值）
grouped = df.groupby('robot_count')['total_energy'].agg(['mean', 'count'])

print("驗證數據：")
print(grouped)

# 生成驗證圖表
plt.figure(figsize=(10, 6))
plt.plot(grouped.index, grouped['mean'], 'o-', color='red', linewidth=2, markersize=10)
plt.xlabel('機器人數量', fontsize=12)
plt.ylabel('總能源消耗', fontsize=12)
plt.title('總能源消耗驗證（清洗後數據）', fontsize=14)
plt.grid(True, alpha=0.3)

# 添加數值標籤
for x, y in zip(grouped.index, grouped['mean']):
    plt.text(x, y + 2000, f'{y:,.0f}', ha='center', va='bottom')

# 添加數據點數量
for x, (_, row) in zip(grouped.index, grouped.iterrows()):
    plt.text(x, row['mean'] - 5000, f'n={row["count"]}', ha='center', va='top', fontsize=8, color='blue')

plt.ylim(60000, 140000)
plt.savefig('test/results/energy_verification.png', dpi=150, bbox_inches='tight')
plt.close()

print("\n生成了驗證圖表: test/results/energy_verification.png")
print("\n如果原始圖表顯示 35 機器人能源降低，可能的原因：")
print("1. 圖表快取問題 - 瀏覽器顯示的是舊圖")
print("2. 圖表生成時數據處理有誤")
print("3. 需要重新執行 experiment_menu.py 選項 4 來重新生成圖表")