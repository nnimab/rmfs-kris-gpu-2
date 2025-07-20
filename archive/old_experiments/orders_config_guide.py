#!/usr/bin/env python3
"""
訂單配置指南 - 支撐 AI 長時間訓練
"""

def calculate_training_requirements():
    """計算 AI 訓練所需的最小訂單數量"""
    
    print("🧠 AI 訓練需求分析")
    print("=" * 50)
    
    # AI 系統訓練需求
    training_requirements = {
        "DQN 快速驗證": {"ticks": 5000, "hours": 1.5},
        "DQN 基本有效": {"ticks": 10000, "hours": 3},
        "DQN 良好效果": {"ticks": 20000, "hours": 6},
        "NERL 快速驗證": {"ticks": 5000, "hours": 1.5},
        "NERL 基本有效": {"ticks": 10000, "hours": 3},
        "NERL 良好效果": {"ticks": 20000, "hours": 6},
    }
    
    for method, req in training_requirements.items():
        print(f"{method:15}: {req['ticks']:6} ticks ({req['hours']:3} 小時)")
    
    print("\n📊 當前配置分析")
    print("=" * 50)
    
    # 當前配置
    current_config = analyze_current_config()
    print(f"總訂單數量: {current_config['total_orders']}")
    print(f"預估運行時間: {current_config['estimated_ticks']} ticks")
    print(f"預估運行小時: {current_config['estimated_hours']:.1f} 小時")
    
    # 判斷是否足夠
    if current_config['estimated_ticks'] >= 20000:
        print("✅ 當前配置足夠支撐所有 AI 訓練需求")
    elif current_config['estimated_ticks'] >= 10000:
        print("🟡 當前配置支撐基本訓練，建議增加以獲得更好效果")
    else:
        print("❌ 當前配置不足，需要增加訂單數量")
        print("\n💡 建議的配置調整:")
        suggest_better_config()

def analyze_current_config():
    """分析當前訂單配置"""
    
    # 連續訂單配置
    continuous_orders = {
        "order_cycle_time": 100,    # 每小時訂單數
        "order_period_time": 5,     # 總小時數
    }
    continuous_total = continuous_orders["order_cycle_time"] * continuous_orders["order_period_time"]
    
    # 積壓訂單配置  
    backlog_orders = {
        "initial_order": 50,        # 積壓訂單數
        "order_cycle_time": 100,    # 每小時訂單數
        "order_period_time": 3,     # 總小時數
    }
    backlog_total = backlog_orders["initial_order"] + (backlog_orders["order_cycle_time"] * backlog_orders["order_period_time"])
    
    total_orders = continuous_total + backlog_total
    
    # 估算運行時間 (1小時 = 3600 ticks)
    max_period = max(continuous_orders["order_period_time"], backlog_orders["order_period_time"])
    estimated_ticks = max_period * 3600
    estimated_hours = max_period
    
    return {
        "continuous_orders": continuous_total,
        "backlog_orders": backlog_total, 
        "total_orders": total_orders,
        "estimated_ticks": estimated_ticks,
        "estimated_hours": estimated_hours
    }

def suggest_better_config():
    """建議更好的配置以支撐長時間訓練"""
    
    print("\n🚀 推薦配置 (支撐 6+ 小時訓練)")
    print("=" * 50)
    
    print("修改 lib/generator/warehouse_generator.py 第 70-90 行:")
    print("""
    # 連續訂單配置 (更多訂單)
    config_orders(
        initial_order=20,
        total_requested_item=500,
        items_orders_class_configuration={"A": 0.6, "B": 0.3, "C": 0.1},
        quantity_range=[1, 12],
        order_cycle_time=150,        # 增加到每小時 150 個訂單
        order_period_time=8,         # 增加到 8 小時 = 1200 個訂單
        order_start_arrival_time=5,
        date=1,
        sim_ver=1,
        dev_mode=False)
    
    # 積壓訂單配置 (更多訂單)
    config_orders(
        initial_order=100,           # 增加積壓訂單到 100 個
        total_requested_item=500,
        items_orders_class_configuration={"A": 0.6, "B": 0.3, "C": 0.1},
        quantity_range=[1, 12],
        order_cycle_time=150,        # 增加到每小時 150 個訂單  
        order_period_time=6,         # 增加到 6 小時 = 900 個訂單
        order_start_arrival_time=5,
        date=1,
        sim_ver=2,
        dev_mode=True)
    """)
    
    print("\n📈 新配置效果:")
    print("- 連續訂單: 150 × 8 = 1,200 個")
    print("- 積壓訂單: 100 + (150 × 6) = 1,000 個") 
    print("- 總訂單數: 2,200 個")
    print("- 運行時間: 8 小時 = 28,800 ticks")
    print("- ✅ 完全支撐所有 AI 訓練需求！")

def create_long_running_config():
    """創建支撐 12+ 小時訓練的配置"""
    
    print("\n🎯 超長訓練配置 (12+ 小時)")
    print("=" * 50)
    
    config_12_hours = """
    # 超長訓練配置
    config_orders(
        order_cycle_time=200,        # 每小時 200 個訂單
        order_period_time=12,        # 12 小時 = 2400 個訂單
        # 其他參數保持不變
    )
    
    # 對應的積壓訂單
    config_orders(
        initial_order=200,           # 200 個積壓訂單
        order_cycle_time=200,        # 每小時 200 個訂單
        order_period_time=10,        # 10 小時 = 2000 個訂單
        # 總共: 200 + 2000 = 2200 個積壓訂單
    )
    """
    
    print(config_12_hours)
    print("📊 超長配置效果:")
    print("- 總訂單: 2400 + 2200 = 4,600 個")
    print("- 運行時間: 12 小時 = 43,200 ticks") 
    print("- 🚀 支撐最高級的 AI 訓練需求！")

def files_to_delete_before_config():
    """需要在配置前刪除的檔案清單"""
    
    print("\n🗑️  修改配置前必須刪除的檔案")
    print("=" * 50)
    
    files_to_delete = [
        "data/input/assign_order.csv",
        "data/output/generated_order.csv", 
        "data/input/generated_backlog.csv",
        "data/output/generated_database_order.csv"
    ]
    
    for file in files_to_delete:
        print(f"❌ {file}")
    
    print("\n💡 刪除這些檔案後，點擊 NetLogo 的 'Setup' 按鈕即可生效！")

if __name__ == "__main__":
    calculate_training_requirements()
    files_to_delete_before_config() 