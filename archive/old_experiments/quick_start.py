#!/usr/bin/env python3
"""
AI 交通控制器快速開始指南
"""

from training_guide import TrainingGuide
import netlogo
import os

def main():
    print("🚀 AI 交通控制器快速開始!")
    print("=" * 50)
    
    guide = TrainingGuide()
    
    while True:
        print("\n選擇操作:")
        print("1️⃣  查看可用模型")
        print("2️⃣  估算訓練時間")
        print("3️⃣  開始 DQN 訓練 (推薦)")
        print("4️⃣  開始 NERL 訓練")
        print("5️⃣  測試已有模型")
        print("6️⃣  比較多個模型")
        print("7️⃣  查看訓練結果")
        print("0️⃣  退出")
        
        choice = input("\n請選擇 (0-7): ").strip()
        
        if choice == "0":
            print("再見！")
            break
            
        elif choice == "1":
            print("\n📁 查看可用模型...")
            netlogo.list_available_models()
            
        elif choice == "2":
            print("\n⏰ 訓練時間估算...")
            controller = input("選擇控制器 (dqn/nerl): ").strip().lower()
            performance = input("目標性能 (basic/good/excellent): ").strip().lower()
            
            if controller in ["dqn", "nerl"] and performance in ["basic", "good", "excellent"]:
                guide.estimate_training_time(controller, performance)
            else:
                print("輸入無效，請重試")
                
        elif choice == "3":
            print("\n🧠 開始 DQN 訓練...")
            ticks = input("訓練時間 (建議: 5000-20000): ").strip()
            
            try:
                ticks = int(ticks)
                if ticks < 1000:
                    print("⚠️  訓練時間太短，建議至少 1000 ticks")
                    continue
                    
                confirm = input(f"確認開始 DQN 訓練 {ticks} ticks? (y/n): ").strip().lower()
                if confirm == "y":
                    guide.dqn_training_workflow(target_ticks=ticks)
                    
            except ValueError:
                print("請輸入有效數字")
                
        elif choice == "4":
            print("\n🧬 開始 NERL 訓練...")
            generations = input("進化代數 (建議: 50-200): ").strip()
            
            try:
                generations = int(generations)
                if generations < 10:
                    print("⚠️  代數太少，建議至少 10 代")
                    continue
                    
                confirm = input(f"確認開始 NERL 訓練 {generations} 代? (y/n): ").strip().lower()
                if confirm == "y":
                    guide.nerl_training_workflow(target_generations=generations)
                    
            except ValueError:
                print("請輸入有效數字")
                
        elif choice == "5":
            print("\n🔍 測試已有模型...")
            controller = input("控制器類型 (dqn/nerl): ").strip().lower()
            model_tick = input("模型時間點 (如: 5000): ").strip()
            
            try:
                model_tick = int(model_tick)
                if controller in ["dqn", "nerl"]:
                    guide.load_and_test_model(controller, model_tick)
                else:
                    print("控制器類型無效")
                    
            except ValueError:
                print("請輸入有效的時間點數字")
                
        elif choice == "6":
            print("\n📊 比較多個模型...")
            models = []
            
            print("請輸入要比較的模型 (輸入 'done' 結束):")
            while True:
                controller = input("控制器類型 (dqn/nerl): ").strip().lower()
                if controller == "done":
                    break
                    
                if controller not in ["dqn", "nerl"]:
                    print("控制器類型無效，請重試")
                    continue
                    
                try:
                    tick = int(input("模型時間點: ").strip())
                    models.append({"type": controller, "tick": tick})
                    print(f"✅ 已添加: {controller} (tick {tick})")
                except ValueError:
                    print("請輸入有效數字")
            
            if models:
                guide.compare_models(models)
            else:
                print("沒有模型可比較")
                
        elif choice == "7":
            print("\n📈 查看訓練結果...")
            print("結果文件位置:")
            print("📊 報告: result/reports/")
            print("📈 圖表: result/charts/")
            print("📋 時間序列: result/time_series/")
            print("🤖 模型: models/")
            
            # 列出最近的報告
            reports_dir = "result/reports"
            if os.path.exists(reports_dir):
                reports = [f for f in os.listdir(reports_dir) if f.endswith('.txt')]
                if reports:
                    print(f"\n最近的報告:")
                    for report in sorted(reports)[-3:]:  # 最近3個
                        print(f"  📄 {report}")
                else:
                    print("沒有找到報告文件")
            else:
                print("報告目錄不存在")
                
        else:
            print("無效選擇，請重試")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  程序中斷")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        print("請檢查 NetLogo 環境是否正確設置") 