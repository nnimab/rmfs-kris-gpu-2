#!/bin/bash

# RMFS 評估管理器 - 模型性能評估與比較
# 支援傳統控制器和 AI 模型的併行評估

# 設定顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 專案目錄 (自動偵測)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 全域變數
SELECTED_CONTROLLERS=()
EVAL_TICKS=20000
NUM_RUNS=3
PARALLEL_EVAL=false

# 自動設置虛擬環境
setup_environment() {
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}創建虛擬環境...${NC}"
        python3.11 -m venv .venv
    fi
    
    echo -e "${GREEN}啟動虛擬環境...${NC}"
    source .venv/bin/activate
    
    # 檢查是否需要安裝套件
    if ! python -c "import torch" 2>/dev/null; then
        echo -e "${YELLOW}安裝依賴套件...${NC}"
        pip install -r requirements.txt
    fi
}

# 自動設置環境
setup_environment

# 設定Python路徑
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# 顯示標題
show_header() {
    clear
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}              RMFS 評估管理器 (模型性能評估)${NC}"
    echo -e "${BLUE}           支援傳統控制器與 AI 模型的比較分析${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

# 顯示系統狀態
show_system_status() {
    echo -e "${GREEN}系統狀態:${NC}"
    echo -e "  專案目錄: $(pwd)"
    echo -e "  Python 版本: $(python --version 2>&1)"
    
    # 檢查GPU狀態
    if command -v nvidia-smi &> /dev/null; then
        gpu_info=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
        echo -e "  GPU: $gpu_info"
    else
        echo -e "  GPU: ${YELLOW}未檢測到${NC}"
    fi
    echo ""
}

# 掃描可用的模型
scan_available_models() {
    echo -e "${BLUE}掃描可用的控制器和模型...${NC}"
    echo ""
    
    # 傳統控制器（總是可用）
    echo -e "${GREEN}傳統控制器:${NC}"
    echo -e "  ${CYAN}[1]${NC} Time-based Controller (固定時間切換)"
    echo -e "  ${CYAN}[2]${NC} Queue-based Controller (基於隊列長度)"
    echo ""
    
    # AI 模型
    echo -e "${GREEN}AI 控制器模型:${NC}"
    
    # DQN 模型
    local model_index=3
    
    # 檢查主要的 DQN 模型
    if [ -f "models/dqn_global_100_final.pth" ]; then
        echo -e "  ${CYAN}[$model_index]${NC} DQN Global (100 episodes) - models/dqn_global_100_final.pth"
        ((model_index++))
    fi
    
    # 檢查 final_models 目錄中的模型
    if [ -d "models/final_models" ]; then
        for model_file in models/final_models/*.pth; do
            if [ -f "$model_file" ]; then
                model_name=$(basename "$model_file" .pth)
                case "$model_name" in
                    "nerl_global_best")
                        echo -e "  ${CYAN}[$model_index]${NC} NERL Global (最佳模型) - $model_file"
                        ;;
                    "nerl_step_best")
                        echo -e "  ${CYAN}[$model_index]${NC} NERL Step (最佳模型) - $model_file"
                        ;;
                    *)
                        echo -e "  ${CYAN}[$model_index]${NC} $model_name - $model_file"
                        ;;
                esac
                ((model_index++))
            fi
        done
    fi
    
    # 檢查 training_runs 中的最新模型
    if [ -d "models/training_runs" ]; then
        echo ""
        echo -e "${YELLOW}訓練歷史模型:${NC}"
        
        # 按日期排序，顯示最新的訓練結果
        for run_dir in $(ls -dt models/training_runs/*/); do
            if [ -f "$run_dir/best_model.pth" ] && [ -f "$run_dir/metadata.json" ]; then
                run_name=$(basename "$run_dir")
                
                # 嘗試從 metadata 讀取訓練資訊
                if command -v jq &> /dev/null; then
                    agent_type=$(jq -r '.agent_type // "unknown"' "$run_dir/metadata.json" 2>/dev/null)
                    reward_mode=$(jq -r '.reward_mode // "unknown"' "$run_dir/metadata.json" 2>/dev/null)
                    variant=$(jq -r '.variant // ""' "$run_dir/metadata.json" 2>/dev/null)
                    
                    desc="$agent_type/$reward_mode"
                    if [ -n "$variant" ] && [ "$variant" != "null" ]; then
                        desc="$desc/$variant"
                    fi
                else
                    # 如果沒有 jq，從目錄名稱猜測
                    desc="$run_name"
                fi
                
                echo -e "  ${CYAN}[$model_index]${NC} $desc - ${run_dir}best_model.pth"
                ((model_index++))
                
                # 只顯示最近的 5 個訓練結果
                if [ $model_index -gt 15 ]; then
                    echo -e "  ${YELLOW}... (更多歷史模型可在 models/training_runs/ 查看)${NC}"
                    break
                fi
            fi
        done
    fi
    
    echo ""
    return $((model_index - 1))
}

# 選擇控制器
select_controllers() {
    local max_index=$1
    SELECTED_CONTROLLERS=()
    
    echo -e "${BLUE}選擇要評估的控制器:${NC}"
    echo -e "${YELLOW}輸入編號（多個編號用空格分隔），或輸入 'all' 評估所有控制器${NC}"
    echo -e "${YELLOW}範例: 1 2 3 或 all${NC}"
    echo ""
    
    read -p "請選擇: " selection
    
    if [ "$selection" = "all" ]; then
        # 選擇所有可用的控制器
        echo -e "${GREEN}已選擇評估所有可用的控制器${NC}"
        
        # 添加傳統控制器
        SELECTED_CONTROLLERS+=("time_based")
        SELECTED_CONTROLLERS+=("queue_based")
        
        # 添加主要的 AI 模型
        if [ -f "models/dqn_global_100_final.pth" ]; then
            SELECTED_CONTROLLERS+=("dqn:models/dqn_global_100_final.pth")
        fi
        
        if [ -f "models/final_models/nerl_global_best.pth" ]; then
            SELECTED_CONTROLLERS+=("nerl:models/final_models/nerl_global_best.pth")
        fi
        
        if [ -f "models/final_models/nerl_step_best.pth" ]; then
            SELECTED_CONTROLLERS+=("nerl:models/final_models/nerl_step_best.pth")
        fi
    else
        # 解析選擇的編號
        for num in $selection; do
            case $num in
                1)
                    SELECTED_CONTROLLERS+=("time_based")
                    echo -e "${GREEN}✓ 已選擇: Time-based Controller${NC}"
                    ;;
                2)
                    SELECTED_CONTROLLERS+=("queue_based")
                    echo -e "${GREEN}✓ 已選擇: Queue-based Controller${NC}"
                    ;;
                *)
                    # 處理 AI 模型選擇
                    if [ $num -ge 3 ] && [ $num -le $max_index ]; then
                        # 這裡需要根據實際掃描結果映射到正確的模型文件
                        # 簡化處理：根據編號推斷模型路徑
                        
                        if [ $num -eq 3 ] && [ -f "models/dqn_global_100_final.pth" ]; then
                            SELECTED_CONTROLLERS+=("dqn:models/dqn_global_100_final.pth")
                            echo -e "${GREEN}✓ 已選擇: DQN Global 模型${NC}"
                        elif [ $num -eq 4 ] && [ -f "models/final_models/nerl_global_best.pth" ]; then
                            SELECTED_CONTROLLERS+=("nerl:models/final_models/nerl_global_best.pth")
                            echo -e "${GREEN}✓ 已選擇: NERL Global 模型${NC}"
                        elif [ $num -eq 5 ] && [ -f "models/final_models/nerl_step_best.pth" ]; then
                            SELECTED_CONTROLLERS+=("nerl:models/final_models/nerl_step_best.pth")
                            echo -e "${GREEN}✓ 已選擇: NERL Step 模型${NC}"
                        else
                            echo -e "${YELLOW}⚠ 編號 $num 的模型映射需要更精確的實現${NC}"
                        fi
                    else
                        echo -e "${RED}✗ 無效的編號: $num${NC}"
                    fi
                    ;;
            esac
        done
    fi
    
    if [ ${#SELECTED_CONTROLLERS[@]} -eq 0 ]; then
        echo -e "${RED}未選擇任何控制器！${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}已選擇 ${#SELECTED_CONTROLLERS[@]} 個控制器進行評估${NC}"
    return 0
}

# 設定評估參數
configure_evaluation() {
    echo -e "${BLUE}評估參數設定:${NC}"
    echo ""
    
    # 設定 tick 數量
    read -p "評估時長 (ticks, 預設 $EVAL_TICKS): " input_ticks
    if [ -n "$input_ticks" ]; then
        EVAL_TICKS=$input_ticks
    fi
    
    # 設定重複次數
    read -p "重複運行次數 (預設 $NUM_RUNS): " input_runs
    if [ -n "$input_runs" ]; then
        NUM_RUNS=$input_runs
    fi
    
    # 是否併行運行
    echo ""
    echo -e "${YELLOW}併行運行可以加快評估速度，但會增加系統負載${NC}"
    read -p "是否啟用併行評估？[y/N]: " parallel_choice
    if [ "$parallel_choice" = "y" ] || [ "$parallel_choice" = "Y" ]; then
        PARALLEL_EVAL=true
        echo -e "${GREEN}✓ 已啟用併行評估${NC}"
    else
        PARALLEL_EVAL=false
        echo -e "${GREEN}✓ 將按順序評估每個控制器${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}評估配置總結:${NC}"
    echo -e "  評估時長: ${GREEN}$EVAL_TICKS ticks${NC}"
    echo -e "  重複次數: ${GREEN}$NUM_RUNS 次${NC}"
    echo -e "  併行模式: ${GREEN}$PARALLEL_EVAL${NC}"
    echo -e "  控制器數: ${GREEN}${#SELECTED_CONTROLLERS[@]} 個${NC}"
    
    # 估算運行時間
    total_runs=$((${#SELECTED_CONTROLLERS[@]} * NUM_RUNS))
    if [ "$PARALLEL_EVAL" = true ]; then
        estimated_time=$(($EVAL_TICKS / 1000 * $NUM_RUNS / 2))  # 併行可以減少時間
    else
        estimated_time=$(($EVAL_TICKS / 1000 * $total_runs / 3))  # 串行運行
    fi
    
    echo -e "  預估時間: ${YELLOW}約 $estimated_time 分鐘${NC}"
    echo ""
}

# 執行評估
run_evaluation() {
    echo -e "${BLUE}開始執行評估...${NC}"
    echo ""
    
    # 創建輸出目錄
    timestamp=$(date +%Y%m%d_%H%M%S)
    output_dir="result/evaluations/EVAL_${timestamp}"
    
    # 構建 Python 評估命令
    eval_command="python evaluate.py"
    eval_command="$eval_command --eval_ticks $EVAL_TICKS"
    eval_command="$eval_command --num_runs $NUM_RUNS"
    eval_command="$eval_command --output_dir $output_dir"
    
    # 添加選擇的控制器
    eval_command="$eval_command --controllers"
    for controller in "${SELECTED_CONTROLLERS[@]}"; do
        eval_command="$eval_command $controller"
    done
    
    # 如果啟用併行，添加併行參數
    if [ "$PARALLEL_EVAL" = true ]; then
        eval_command="$eval_command --parallel"
    fi
    
    # 顯示即將執行的命令
    echo -e "${CYAN}執行命令:${NC}"
    echo -e "${YELLOW}$eval_command${NC}"
    echo ""
    
    # 詢問是否在後台運行
    read -p "是否在後台運行（使用 screen）？[Y/n]: " background_choice
    
    if [ "$background_choice" != "n" ] && [ "$background_choice" != "N" ]; then
        # 後台運行
        screen_name="rmfs_eval_${timestamp}"
        
        screen -dmS "$screen_name" bash -c "
            cd $PROJECT_DIR
            source .venv/bin/activate
            export PYTHONPATH=$PROJECT_DIR:\$PYTHONPATH
            
            echo '==============================================='
            echo 'RMFS 評估任務'
            echo '時間: \$(date)'
            echo '輸出目錄: $output_dir'
            echo '==============================================='
            
            $eval_command
            
            echo ''
            echo '==============================================='
            echo '評估完成時間: \$(date)'
            echo '結果保存在: $output_dir'
            echo '==============================================='
            echo ''
            echo '按任意鍵結束...'
            read
        "
        
        echo -e "${GREEN}✅ 評估任務已在後台啟動！${NC}"
        echo -e "${BLUE}Screen 會話名稱: $screen_name${NC}"
        echo -e "${BLUE}查看進度: screen -r $screen_name${NC}"
        echo -e "${BLUE}結果將保存在: $output_dir${NC}"
    else
        # 前台運行
        echo -e "${GREEN}在前台執行評估...${NC}"
        
        # 創建輸出目錄
        mkdir -p "$output_dir"
        
        # 執行評估
        $eval_command
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ 評估完成！${NC}"
            echo -e "${BLUE}結果保存在: $output_dir${NC}"
            
            # 提示生成視覺化
            echo ""
            read -p "是否立即生成視覺化圖表？[Y/n]: " viz_choice
            if [ "$viz_choice" != "n" ] && [ "$viz_choice" != "N" ]; then
                generate_visualizations "$output_dir"
            fi
        else
            echo -e "${RED}❌ 評估過程中發生錯誤${NC}"
        fi
    fi
}

# 生成視覺化圖表
generate_visualizations() {
    local result_dir=$1
    
    echo -e "${BLUE}生成視覺化圖表...${NC}"
    
    if [ -f "visualization_generator.py" ]; then
        python visualization_generator.py "$result_dir"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 視覺化圖表生成完成！${NC}"
            echo -e "${BLUE}圖表保存在: $result_dir/visualizations/${NC}"
        else
            echo -e "${RED}❌ 視覺化生成失敗${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ 未找到 visualization_generator.py${NC}"
    fi
}

# 查看評估歷史
view_evaluation_history() {
    echo -e "${BLUE}評估歷史記錄:${NC}"
    echo ""
    
    if [ ! -d "result/evaluations" ]; then
        echo -e "${YELLOW}尚無評估記錄${NC}"
        return 1
    fi
    
    # 列出最近的評估結果
    eval_dirs=$(ls -dt result/evaluations/EVAL_* 2>/dev/null | head -10)
    
    if [ -z "$eval_dirs" ]; then
        echo -e "${YELLOW}尚無評估記錄${NC}"
        return 1
    fi
    
    echo -e "${GREEN}最近的評估結果:${NC}"
    index=1
    for dir in $eval_dirs; do
        dir_name=$(basename "$dir")
        timestamp=$(echo "$dir_name" | sed 's/EVAL_//')
        
        # 嘗試讀取評估摘要
        if [ -f "$dir/evaluation_summary.json" ]; then
            # 如果有摘要文件，顯示更多資訊
            echo -e "  ${CYAN}[$index]${NC} $timestamp - $dir"
        else
            echo -e "  ${CYAN}[$index]${NC} $timestamp - $dir"
        fi
        ((index++))
    done
    
    echo ""
    read -p "選擇要查看的評估結果 (編號) 或按 Enter 返回: " choice
    
    if [ -n "$choice" ] && [ "$choice" -ge 1 ] && [ "$choice" -lt "$index" ]; then
        selected_dir=$(echo "$eval_dirs" | sed -n "${choice}p")
        
        echo ""
        echo -e "${BLUE}評估結果: $selected_dir${NC}"
        
        # 顯示結果文件
        if [ -d "$selected_dir" ]; then
            echo -e "${GREEN}包含的文件:${NC}"
            ls -la "$selected_dir" | grep -v "^total" | grep -v "^d" | while read line; do
                filename=$(echo "$line" | awk '{print $9}')
                if [ -n "$filename" ]; then
                    echo -e "  • $filename"
                fi
            done
            
            # 如果有摘要文件，顯示關鍵指標
            if [ -f "$selected_dir/evaluation_summary.txt" ]; then
                echo ""
                echo -e "${BLUE}評估摘要:${NC}"
                head -20 "$selected_dir/evaluation_summary.txt"
            fi
        fi
    fi
}

# 顯示正在運行的評估任務
show_running_evaluations() {
    echo -e "${BLUE}正在運行的評估任務:${NC}"
    
    # 檢查 screen 會話
    sessions=$(screen -ls | grep "rmfs_eval" | wc -l)
    if [ $sessions -eq 0 ]; then
        echo -e "${YELLOW}  無正在運行的評估任務${NC}"
    else
        echo -e "${GREEN}  找到 $sessions 個正在運行的評估任務:${NC}"
        screen -ls | grep "rmfs_eval" | while read line; do
            session_name=$(echo $line | awk '{print $1}')
            echo -e "${GREEN}    - $session_name${NC}"
        done
        
        echo ""
        echo -e "${BLUE}提示: 使用 'screen -r <session_name>' 查看任務進度${NC}"
    fi
    echo ""
}

# 主選單
show_main_menu() {
    echo -e "${BLUE}=== 主選單 ===${NC}"
    echo ""
    echo -e "${GREEN}評估選項:${NC}"
    echo "  [1] 執行新的評估"
    echo "  [2] 查看評估歷史"
    echo "  [3] 查看正在運行的評估"
    echo ""
    echo -e "${CYAN}快速評估:${NC}"
    echo "  [4] 快速評估所有控制器 (5000 ticks)"
    echo "  [5] 標準評估所有控制器 (20000 ticks)"
    echo "  [6] 完整評估所有控制器 (50000 ticks)"
    echo ""
    echo -e "${RED}其他選項:${NC}"
    echo "  [0] 離開"
    echo ""
    echo -e "${BLUE}================================================================${NC}"
}

# 快速評估函數
quick_evaluation() {
    local ticks=$1
    local desc=$2
    
    echo -e "${BLUE}執行${desc}...${NC}"
    echo -e "${YELLOW}評估參數: $ticks ticks, 3 次重複${NC}"
    
    # 設定所有控制器
    SELECTED_CONTROLLERS=("time_based" "queue_based")
    
    if [ -f "models/dqn_global_100_final.pth" ]; then
        SELECTED_CONTROLLERS+=("dqn:models/dqn_global_100_final.pth")
    fi
    
    if [ -f "models/final_models/nerl_global_best.pth" ]; then
        SELECTED_CONTROLLERS+=("nerl:models/final_models/nerl_global_best.pth")
    fi
    
    if [ -f "models/final_models/nerl_step_best.pth" ]; then
        SELECTED_CONTROLLERS+=("nerl:models/final_models/nerl_step_best.pth")
    fi
    
    EVAL_TICKS=$ticks
    NUM_RUNS=3
    PARALLEL_EVAL=true
    
    run_evaluation
}

# 主迴圈
main() {
    while true; do
        show_header
        show_system_status
        show_running_evaluations
        show_main_menu
        
        read -p "請選擇 [0-6]: " choice
        
        case $choice in
            1)
                # 執行新的評估
                scan_available_models
                max_index=$?
                
                if select_controllers $max_index; then
                    configure_evaluation
                    
                    echo ""
                    read -p "確認開始評估？[Y/n]: " confirm
                    if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
                        run_evaluation
                    else
                        echo -e "${YELLOW}已取消評估${NC}"
                    fi
                fi
                ;;
            2)
                # 查看評估歷史
                view_evaluation_history
                ;;
            3)
                # 查看正在運行的評估（會自動顯示）
                ;;
            4)
                # 快速評估 (5000 ticks)
                quick_evaluation 5000 "快速評估"
                ;;
            5)
                # 標準評估 (20000 ticks)
                quick_evaluation 20000 "標準評估"
                ;;
            6)
                # 完整評估 (50000 ticks)
                quick_evaluation 50000 "完整評估"
                ;;
            0)
                echo -e "${GREEN}感謝使用 RMFS 評估管理器！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}無效的選擇，請重新輸入${NC}"
                ;;
        esac
        
        echo ""
        echo -e "${YELLOW}按任意鍵繼續...${NC}"
        read
    done
}

# 檢查必要工具
if ! command -v screen &> /dev/null; then
    echo -e "${YELLOW}提示: 安裝 screen 可以支援後台運行功能${NC}"
    echo -e "${YELLOW}安裝命令: sudo apt-get install screen${NC}"
fi

# 啟動主程式
main