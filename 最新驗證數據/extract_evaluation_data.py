import json
import os
import pandas as pd
from pathlib import Path

def extract_evaluation_data(base_path):
    """提取所有實驗組別的評估數據"""
    results = []
    
    # 實驗組別清單
    experiment_groups = [
        "dqn_dqn_model_global_55000",
        "dqn_dqn_model_step_55000",
        "nerl_nerl_global_a3000ticks",
        "nerl_nerl_global_a8000ticks",
        "nerl_nerl_global_b3000ticks",
        "nerl_nerl_global_b8000ticks",
        "nerl_nerl_step_a3000ticks",
        "nerl_nerl_step_a8000ticks",
        "nerl_nerl_step_b3000ticks",
        "nerl_nerl_step_b8000ticks",
        "no_controller",
        "queue_based",
        "time_based"
    ]
    
    for group in experiment_groups:
        group_path = Path(base_path) / "RUN2_1" / group
        
        if not group_path.exists():
            print(f"警告: {group} 資料夾不存在")
            continue
            
        # 收集每個RUN的數據
        run_data = {
            "Experiment Group": group,
            "Completion Rate (Run 1)": None,
            "Completion Rate (Run 2)": None,
            "Completion Rate (Run 3)": None,
            "Completion Rate (Run 4)": None,
            "Energy per Order (Run 1)": None,
            "Energy per Order (Run 2)": None,
            "Energy per Order (Run 3)": None,
            "Energy per Order (Run 4)": None,
            "Total Energy (Run 1)": None,
            "Total Energy (Run 2)": None,
            "Total Energy (Run 3)": None,
            "Total Energy (Run 4)": None,
            "Signal Switches (Run 1)": None,
            "Signal Switches (Run 2)": None,
            "Signal Switches (Run 3)": None,
            "Signal Switches (Run 4)": None,
            "Completed Orders (Run 1)": None,
            "Completed Orders (Run 2)": None,
            "Completed Orders (Run 3)": None,
            "Completed Orders (Run 4)": None
        }
        
        # 檢查每個RUN (RUN_1 到 RUN_4)
        for run_num in range(1, 5):
            run_folder = group_path / f"RUN_{run_num}"
            
            if run_folder.exists():
                # 找到該RUN資料夾下的子資料夾
                subdirs = [d for d in run_folder.iterdir() if d.is_dir()]
                
                if subdirs:
                    # 假設每個RUN只有一個子資料夾
                    subdir = subdirs[0]
                    json_file = subdir / "evaluation_results.json"
                    
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                            if "results" in data and len(data["results"]) > 0:
                                result = data["results"][0]
                                
                                # 提取關鍵數據
                                run_data[f"Completion Rate (Run {run_num})"] = result.get("completion_rate")
                                run_data[f"Energy per Order (Run {run_num})"] = result.get("energy_per_order")
                                run_data[f"Total Energy (Run {run_num})"] = result.get("total_energy")
                                run_data[f"Signal Switches (Run {run_num})"] = result.get("signal_switch_count")
                                run_data[f"Completed Orders (Run {run_num})"] = result.get("completed_orders")
                                
                                print(f"成功讀取 {group} RUN_{run_num} 的數據")
                        except Exception as e:
                            print(f"讀取 {group} RUN_{run_num} 時發生錯誤: {e}")
                    else:
                        print(f"找不到 {group} RUN_{run_num} 的 evaluation_results.json")
                else:
                    print(f"{group} RUN_{run_num} 沒有子資料夾")
            else:
                print(f"{group} 沒有 RUN_{run_num} 資料夾")
        
        results.append(run_data)
    
    return results

def main():
    base_path = r"C:\Users\h2388\Desktop\論文簡報\最新驗證數據"
    
    print("開始提取評估數據...")
    results = extract_evaluation_data(base_path)
    
    # 建立DataFrame
    df = pd.DataFrame(results)
    
    # 儲存為CSV檔案
    output_file = os.path.join(base_path, "evaluation_summary_table.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n數據已儲存到: {output_file}")
    
    # 也儲存為Excel檔案（更易讀）
    excel_file = os.path.join(base_path, "evaluation_summary_table.xlsx")
    df.to_excel(excel_file, index=False)
    print(f"數據也已儲存到: {excel_file}")
    
    # 顯示前幾行數據
    print("\n數據預覽:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    df = main()