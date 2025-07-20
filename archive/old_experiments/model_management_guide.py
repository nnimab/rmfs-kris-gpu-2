#!/usr/bin/env python3
"""
模型管理指南 - 載入、繼續訓練、數據分析
"""

import os
import json
import pandas as pd
from datetime import datetime

def analyze_existing_models():
    """分析現有的模型和訓練數據"""
    
    print("🔍 現有模型分析")
    print("=" * 60)
    
    # 檢查模型文件
    models_dir = "models"
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
        
        print("📁 可用模型:")
        dqn_models = []
        nerl_models = []
        
        for model_file in model_files:
            file_size = os.path.getsize(os.path.join(models_dir, model_file)) / 1024  # KB
            
            if model_file.startswith('dqn_traffic_'):
                tick = model_file.replace('dqn_traffic_', '').replace('.pth', '')
                dqn_models.append({"tick": tick, "file": model_file, "size": file_size})
                
            elif model_file.startswith('nerl_traffic'):
                if '_' in model_file:
                    tick = model_file.replace('nerl_traffic_', '').replace('.pth', '')
                else:
                    tick = "latest"
                nerl_models.append({"tick": tick, "file": model_file, "size": file_size})
        
        # 顯示 DQN 模型
        if dqn_models:
            print("\\n🧠 DQN 模型:")
            for model in sorted(dqn_models, key=lambda x: int(x["tick"]) if x["tick"].isdigit() else 0):
                print(f"  ✅ Tick {model['tick']:>6}: {model['file']} ({model['size']:.1f} KB)")
        
        # 顯示 NERL 模型  
        if nerl_models:
            print("\\n🧬 NERL 模型:")
            for model in nerl_models:
                print(f"  ✅ Tick {model['tick']:>6}: {model['file']} ({model['size']:.1f} KB)")
                
        return {"dqn": dqn_models, "nerl": nerl_models}
    else:
        print("❌ 沒有找到 models 目錄")
        return {"dqn": [], "nerl": []}

def analyze_training_data():
    """分析訓練數據和報告"""
    
    print("\\n📊 訓練數據分析")
    print("=" * 60)
    
    # 檢查性能總結
    summary_file = "result/reports/performance_summary.csv"
    if os.path.exists(summary_file):
        df = pd.read_csv(summary_file)
        print("📈 性能總結 (最近5次訓練):")
        print(df.tail().to_string(index=False))
        
        # 分析最佳性能
        if len(df) > 0:
            best_energy = df.loc[df['total_energy_consumption'].idxmin()]
            best_orders = df.loc[df['completed_orders_count'].idxmax()]
            
            print("\\n🏆 最佳性能記錄:")
            print(f"  最低能耗: {best_energy['total_energy_consumption']:.2f} (完成訂單: {best_energy['completed_orders_count']})")
            print(f"  最多訂單: {best_orders['completed_orders_count']} (能耗: {best_orders['total_energy_consumption']:.2f})")
    
    # 檢查時間序列數據
    time_series_dir = "result/time_series"
    if os.path.exists(time_series_dir):
        ts_files = [f for f in os.listdir(time_series_dir) if f.endswith('.json')]
        if ts_files:
            print(f"\\n📋 時間序列數據: {len(ts_files)} 個文件")
            
            # 分析最新的時間序列文件
            latest_file = max(ts_files, key=lambda x: os.path.getmtime(os.path.join(time_series_dir, x)))
            file_path = os.path.join(time_series_dir, latest_file)
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if data:
                    print(f"  📄 最新文件: {latest_file}")
                    print(f"  📊 數據點數: {len(data)}")
                    
                    # 分析訓練進度
                    if len(data) > 10:
                        recent_data = data[-10:]  # 最近10個數據點
                        avg_energy = sum(d.get('total_energy_consumption', 0) for d in recent_data) / len(recent_data)
                        avg_orders = sum(d.get('completed_orders_count', 0) for d in recent_data) / len(recent_data)
                        
                        print(f"  📈 最近表現: 平均能耗 {avg_energy:.2f}, 平均完成訂單 {avg_orders:.1f}")
                        
            except Exception as e:
                print(f"  ❌ 無法讀取時間序列數據: {e}")

def recommend_best_model():
    """推薦最佳的模型用於繼續訓練"""
    
    print("\\n💡 模型推薦")
    print("=" * 60)
    
    models = analyze_existing_models()
    
    # DQN 推薦
    if models["dqn"]:
        latest_dqn = max(models["dqn"], key=lambda x: int(x["tick"]) if x["tick"].isdigit() else 0)
        print(f"🧠 DQN 推薦: 載入 tick {latest_dqn['tick']} 的模型")
        print(f"   理由: 最新訓練的模型，包含最多的學習經驗")
        
        # 如果有多個模型，也推薦中間的
        if len(models["dqn"]) > 1:
            mid_tick = sorted([int(m["tick"]) for m in models["dqn"] if m["tick"].isdigit()])[len(models["dqn"])//2]
            print(f"   替代選擇: tick {mid_tick} (如果最新模型過擬合)")
    
    # NERL 推薦
    if models["nerl"]:
        print(f"🧬 NERL 推薦: 載入最新的 nerl_traffic.pth")
        print(f"   理由: NERL 通常保存最佳個體，可直接繼續進化")

def create_continue_training_script():
    """創建繼續訓練的腳本"""
    
    print("\\n🚀 繼續訓練指南")
    print("=" * 60)
    
    print("方法1: 使用 NetLogo 界面")
    print("1. 打開 NetLogo")
    print("2. 設置控制器並載入模型:")
    print("   - DQN: 設置 model-tick 為想要的時間點 (如 10000)")
    print("   - 點擊 'set-dqn-with-model' 按鈕")
    print("   - 或者 NERL: 直接點擊 'set-nerl-controller'")
    print("3. 開始運行: 點擊 'go' 按鈕")
    
    print("\\n方法2: 使用 Python 腳本")
    print("```python")
    print("import netlogo")
    print("")
    print("# 載入 DQN 模型並繼續訓練")
    print("netlogo.setup()")
    print("netlogo.set_dqn_controller(exploration_rate=0.3, load_model_tick=10000)")
    print("netlogo.set_dqn_training_mode(is_training=True)")
    print("")
    print("# 或載入 NERL 模型並繼續訓練")
    print("# netlogo.set_nerl_controller()")
    print("# netlogo.set_nerl_training_mode(is_training=True)")
    print("")
    print("# 繼續訓練")
    print("for i in range(10000):  # 再訓練 10000 ticks")
    print("    netlogo.tick()")
    print("    if i % 1000 == 0:")
    print("        print(f'Progress: {i}/10000 ticks')")
    print("```")

def create_model_comparison_script():
    """創建模型比較腳本"""
    
    print("\\n📊 模型比較指南")
    print("=" * 60)
    
    print("比較不同時間點的模型性能:")
    print("```python")
    print("from training_guide import TrainingGuide")
    print("")
    print("guide = TrainingGuide()")
    print("")
    print("# 比較多個 DQN 模型")
    print("models_to_compare = [")
    print("    {'type': 'dqn', 'tick': 5000},")
    print("    {'type': 'dqn', 'tick': 10000},")
    print("    {'type': 'nerl', 'tick': 'latest'}")
    print("]")
    print("")
    print("guide.compare_models(models_to_compare, test_duration=2000)")
    print("```")

def backup_current_models():
    """備份當前模型"""
    
    print("\\n💾 模型備份建議")
    print("=" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"models_backup_{timestamp}"
    
    print(f"建議創建備份目錄: {backup_dir}")
    print("備份命令:")
    print(f"mkdir {backup_dir}")
    print(f"copy models\\*.pth {backup_dir}\\")
    print(f"copy result\\reports\\performance_summary.csv {backup_dir}\\")
    
    print("\\n這樣可以:")
    print("✅ 保護現有的訓練成果")
    print("✅ 允許安全地進行新實驗")
    print("✅ 比較不同版本的模型")

if __name__ == "__main__":
    print("🎯 AI 模型管理完整指南")
    print("=" * 80)
    
    # 分析現有資源
    models = analyze_existing_models()
    analyze_training_data()
    
    # 提供建議
    recommend_best_model()
    create_continue_training_script()
    create_model_comparison_script()
    backup_current_models()
    
    print("\\n" + "=" * 80)
    print("🎉 你有豐富的訓練數據！可以立即開始繼續訓練或進行模型比較！") 