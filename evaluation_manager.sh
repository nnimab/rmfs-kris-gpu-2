#!/bin/bash

# RMFS 評估管理器 V2 - 改進的模型映射系統
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

# 用於存儲所有可用的控制器資訊
declare -a CONTROLLER_LIST
declare -a CONTROLLER_DISPLAY
declare -a CONTROLLER_SPEC

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
    echo -e "${BLUE}              RMFS 評估管理器 V2 (改進版)${NC}"
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

# 掃描可用的模型 (改進版)
scan_available_models() {
    echo -e "${BLUE}掃描可用的控制器和模型...${NC}"
    echo ""
    
    # 重置陣列
    CONTROLLER_LIST=()
    CONTROLLER_DISPLAY=()
    CONTROLLER_SPEC=()
    
    local index=1
    
    # 傳統控制器
    echo -e "${GREEN}傳統控制器:${NC}"
    
    CONTROLLER_LIST+=("$index")
    CONTROLLER_DISPLAY+=("Time-based Controller (固定時間切換)")
    CONTROLLER_SPEC+=("time_based")
    echo -e "  ${CYAN}[$index]${NC} Time-based Controller (固定時間切換)"
    ((index++))
    
    CONTROLLER_LIST+=("$index")
    CONTROLLER_DISPLAY+=("Queue-based Controller (基於隊列長度)")
    CONTROLLER_SPEC+=("queue_based")
    echo -e "  ${CYAN}[$index]${NC} Queue-based Controller (基於隊列長度)"
    ((index++))
    
    echo ""
    
    # AI 模型
    echo -e "${GREEN}AI 控制器模型:${NC}"
    
    # 檢查主要的模型文件
    if [ -f "models/dqn_global_100_final.pth" ]; then
        CONTROLLER_LIST+=("$index")
        CONTROLLER_DISPLAY+=("DQN Global (100 episodes)")
        CONTROLLER_SPEC+=("dqn:models/dqn_global_100_final.pth")
        echo -e "  ${CYAN}[$index]${NC} DQN Global (100 episodes) - models/dqn_global_100_final.pth"
        ((index++))
    fi
    
    # 檢查 final_models 目錄
    if [ -d "models/final_models" ]; then
        for model_file in models/final_models/*.pth; do
            if [ -f "$model_file" ]; then
                model_name=$(basename "$model_file" .pth)
                
                # 判斷模型類型和描述
                case "$model_name" in
                    "nerl_global_best")
                        display_name="NERL Global (最佳模型)"
                        controller_type="nerl"
                        ;;
                    "nerl_step_best")
                        display_name="NERL Step (最佳模型)"
                        controller_type="nerl"
                        ;;
                    *"dqn"*)
                        display_name="DQN $(echo $model_name | sed 's/_/ /g')"
                        controller_type="dqn"
                        ;;
                    *"nerl"*)
                        display_name="NERL $(echo $model_name | sed 's/_/ /g')"
                        controller_type="nerl"
                        ;;
                    *)
                        display_name="$model_name"
                        controller_type="unknown"
                        ;;
                esac
                
                CONTROLLER_LIST+=("$index")
                CONTROLLER_DISPLAY+=("$display_name")
                CONTROLLER_SPEC+=("$controller_type:$model_file")
                echo -e "  ${CYAN}[$index]${NC} $display_name - $model_file"
                ((index++))
            fi
        done
    fi
    
    # 檢查 training_runs 目錄
    if [ -d "models/training_runs" ] && [ "$(ls -A models/training_runs 2>/dev/null)" ]; then
        echo ""
        echo -e "${YELLOW}訓練歷史模型:${NC}"
        
        local count=0
        for run_dir in $(ls -dt models/training_runs/*/); do
            run_name=$(basename "$run_dir")
            
            # 掃描該目錄下的所有 .pth 檔案（不進入子目錄）
            for pth_file in "$run_dir"*.pth; do
                if [ -f "$pth_file" ]; then
                    pth_name=$(basename "$pth_file")
                    
                    # 從 metadata 或目錄名稱判斷類型
                    if [ -f "$run_dir/metadata.json" ] && command -v jq &> /dev/null; then
                        agent_type=$(jq -r '.agent_type // "unknown"' "$run_dir/metadata.json" 2>/dev/null)
                        reward_mode=$(jq -r '.reward_mode // "unknown"' "$run_dir/metadata.json" 2>/dev/null)
                        variant=$(jq -r '.variant // ""' "$run_dir/metadata.json" 2>/dev/null)
                        
                        desc="$agent_type/$reward_mode"
                        if [ -n "$variant" ] && [ "$variant" != "null" ]; then
                            desc="$desc/$variant"
                        fi
                    else
                        # 從目錄名稱提取資訊
                        if [[ "$run_name" == *"nerl"* ]]; then
                            agent_type="nerl"
                        elif [[ "$run_name" == *"dqn"* ]]; then
                            agent_type="dqn"
                        else
                            agent_type="unknown"
                        fi
                        desc="$run_name"
                    fi
                    
                    # 添加到列表
                    CONTROLLER_LIST+=("$index")
                    CONTROLLER_DISPLAY+=("$desc - $pth_name")
                    CONTROLLER_SPEC+=("$agent_type:$pth_file")
                    echo -e "  ${CYAN}[$index]${NC} $desc - $pth_name"
                    ((index++))
                    ((count++))
                    
                    # 限制每個目錄只顯示前幾個 pth 檔案
                    if [ $count -ge 3 ]; then
                        break
                    fi
                fi
            done
            
            # 限制總顯示數量
            if [ $count -ge 15 ]; then
                echo -e "  ${YELLOW}... (更多歷史模型可在 models/training_runs/ 查看)${NC}"
                break
            fi
        done
    fi
    
    echo ""
    echo -e "${BLUE}共找到 $((index-1)) 個可用的控制器/模型${NC}"
    return $((index-1))
}

# 選擇控制器 (改進版)
select_controllers() {
    local max_index=$1
    SELECTED_CONTROLLERS=()
    
    echo ""
    echo -e "${BLUE}選擇要評估的控制器:${NC}"
    echo -e "${YELLOW}輸入編號（多個編號用空格分隔），或輸入 'all' 評估所有控制器${NC}"
    echo -e "${YELLOW}範例: 1 2 3 或 all${NC}"
    echo ""
    
    read -p "請選擇: " selection
    echo ""
    
    if [ "$selection" = "all" ]; then
        # 選擇所有控制器
        echo -e "${GREEN}已選擇評估所有可用的控制器${NC}"
        for i in "${!CONTROLLER_SPEC[@]}"; do
            SELECTED_CONTROLLERS+=("${CONTROLLER_SPEC[$i]}")
        done
    else
        # 解析選擇的編號
        for num in $selection; do
            # 檢查編號是否有效
            local found=false
            for i in "${!CONTROLLER_LIST[@]}"; do
                if [ "${CONTROLLER_LIST[$i]}" = "$num" ]; then
                    SELECTED_CONTROLLERS+=("${CONTROLLER_SPEC[$i]}")
                    echo -e "${GREEN}✓ 已選擇: ${CONTROLLER_DISPLAY[$i]}${NC}"
                    found=true
                    break
                fi
            done
            
            if [ "$found" = false ]; then
                echo -e "${RED}✗ 無效的編號: $num${NC}"
            fi
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

# 其餘功能保持不變...
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
        estimated_time=$(($EVAL_TICKS / 1000 * $NUM_RUNS / 2))
    else
        estimated_time=$(($EVAL_TICKS / 1000 * $total_runs / 3))
    fi
    
    echo -e "  預估時間: ${YELLOW}約 $estimated_time 分鐘${NC}"
    echo ""
}

# 執行評估
run_evaluation() {
    echo -e "${BLUE}開始執行評估...${NC}"
    echo ""
    
    # 詢問運行模式
    echo -e "${YELLOW}選擇評估模式:${NC}"
    echo -e "  [1] 單一會話模式 (所有模型在同一個 screen 會話中評估)"
    echo -e "  [2] 多會話模式 (每個模型獨立的 screen 會話)"
    echo ""
    read -p "請選擇 [1-2] (預設: 1): " eval_mode
    eval_mode=${eval_mode:-1}
    
    if [ "$eval_mode" = "1" ]; then
        # 原本的單一會話模式
        run_single_session_evaluation
    elif [ "$eval_mode" = "2" ]; then
        # 新的多會話模式
        run_multi_session_evaluation
    else
        echo -e "${RED}無效的選擇${NC}"
        return 1
    fi
}

# 單一會話評估（原本的邏輯）
run_single_session_evaluation() {
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
    # 注意：多會話模式下不需要 --parallel，因為每個 screen 已經是獨立進程
    if [ "$PARALLEL_EVAL" = true ] && [ "$enable_multi_session" = false ]; then
        eval_command="$eval_command --parallel"
        echo -e "${YELLOW}⚡ 並行模式已啟用（單一會話內部並行）${NC}"
    elif [ "$PARALLEL_EVAL" = true ] && [ "$enable_multi_session" = true ]; then
        echo -e "${YELLOW}⚠️  注意：多會話模式已經是並行執行，--parallel 參數將被忽略${NC}"
        echo -e "${YELLOW}   每個模型在獨立的 screen 會話中運行${NC}"
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
            export LANG=zh_TW.UTF-8
            export LC_ALL=zh_TW.UTF-8
            
            echo '==============================================='
            echo 'RMFS 評估任務 (單一會話)'
            echo \"時間: \$(date)\"
            echo \"輸出目錄: $output_dir\"
            echo '==============================================='
            
            # 創建輸出目錄
            mkdir -p $output_dir
            
            echo \"執行命令: $eval_command\"
            echo ''
            
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

# 多會話評估（每個模型獨立會話）
run_multi_session_evaluation() {
    echo -e "${BLUE}多會話模式：為每個模型創建獨立的 screen 會話${NC}"
    echo ""
    
    # 基礎時間戳
    base_timestamp=$(date +%Y%m%d_%H%M%S)
    
    # 為每個控制器創建獨立的評估會話
    local session_count=0
    for i in "${!SELECTED_CONTROLLERS[@]}"; do
        controller="${SELECTED_CONTROLLERS[$i]}"
        
        # 生成會話名稱
        if [[ "$controller" == *":"* ]]; then
            # AI 模型：提取檔名
            model_type=$(echo "$controller" | cut -d':' -f1)
            model_path=$(echo "$controller" | cut -d':' -f2-)
            model_name=$(basename "$model_path" .pth)
            # 清理檔名中的特殊字符
            clean_name=$(echo "$model_name" | sed 's/[^a-zA-Z0-9_-]/_/g' | cut -c1-20)
            screen_session="rmfs_${model_type}_${clean_name}_${base_timestamp}"
            display_name="${model_type}: ${model_name}.pth"
        else
            # 傳統控制器
            screen_session="rmfs_${controller}_${base_timestamp}"
            display_name="$controller"
        fi
        
        # 創建輸出目錄（簡化路徑）
        if [[ "$controller" == *":"* ]]; then
            # 從控制器規格提取簡化名稱
            controller_simple=$(echo "$controller" | cut -d':' -f1)
            model_basename=$(basename "$(echo "$controller" | cut -d':' -f2-)" .pth)
            output_dir="result/evaluations/EVAL_${controller_simple}_${model_basename}_${base_timestamp}"
        else
            output_dir="result/evaluations/EVAL_${controller}_${base_timestamp}"
        fi
        
        # 構建單個控制器的評估命令
        eval_command="python evaluate.py"
        eval_command="$eval_command --eval_ticks $EVAL_TICKS"
        eval_command="$eval_command --num_runs $NUM_RUNS"
        eval_command="$eval_command --output_dir $output_dir"
        eval_command="$eval_command --controllers $controller"
        
        # 創建 screen 會話
        screen -dmS "$screen_session" bash -c "
            cd $PROJECT_DIR
            source .venv/bin/activate
            export PYTHONPATH=$PROJECT_DIR:\$PYTHONPATH
            export LANG=zh_TW.UTF-8
            export LC_ALL=zh_TW.UTF-8
            
            echo '==============================================='
            echo 'RMFS 評估任務 - 多會話模式'
            echo \"控制器: $display_name\"
            echo \"會話名稱: $screen_session\"
            echo \"時間: \$(date)\"
            echo \"輸出目錄: $output_dir\"
            echo '==============================================='
            echo ''
            
            # 創建輸出目錄
            mkdir -p $output_dir
            
            echo \"執行命令: $eval_command\"
            echo ''
            
            $eval_command
            
            echo ''
            echo '==============================================='
            echo \"評估完成時間: \$(date)\"
            echo \"控制器: $display_name\"
            echo \"結果保存在: $output_dir\"
            echo '==============================================='
            echo ''
            echo '按任意鍵結束...'
            read
        "
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 啟動評估: $display_name${NC}"
            echo -e "${CYAN}   會話: $screen_session${NC}"
            ((session_count++))
        else
            echo -e "${RED}❌ 無法啟動評估: $display_name${NC}"
        fi
        
        # 稍微延遲以避免同時啟動太多進程
        sleep 1
    done
    
    echo ""
    echo -e "${GREEN}✅ 已啟動 $session_count 個評估會話${NC}"
    echo ""
    echo -e "${BLUE}提示:${NC}"
    echo -e "${BLUE}  • 使用選項 [3] 查看和連接到各個會話${NC}"
    echo -e "${BLUE}  • 使用 'screen -ls' 查看所有會話${NC}"
    echo -e "${BLUE}  • 每個模型的結果會保存在獨立的目錄${NC}"
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
            
            # 顯示評估的模型
            if [ -f "$selected_dir/evaluation_summary.json" ]; then
                echo ""
                echo -e "${BLUE}評估的控制器:${NC}"
                if command -v jq &> /dev/null; then
                    controllers=$(jq -r '.controllers_evaluated[]' "$selected_dir/evaluation_summary.json" 2>/dev/null)
                    echo "$controllers" | while read controller; do
                        # 從控制器名稱提取模型路徑
                        if [[ "$controller" == *":"* ]]; then
                            model_type=$(echo "$controller" | cut -d':' -f1)
                            model_path=$(echo "$controller" | cut -d':' -f2-)
                            model_name=$(basename "$model_path")
                            echo -e "  • ${CYAN}$model_type${NC}: $model_name"
                        else
                            echo -e "  • ${CYAN}$controller${NC}"
                        fi
                    done
                else
                    # 如果沒有 jq，嘗試用 grep
                    grep -o '"[^"]*"' "$selected_dir/evaluation_summary.json" | grep -E "time_based|queue_based|dqn:|nerl:" | while read controller; do
                        controller=$(echo $controller | tr -d '"')
                        echo -e "  • ${CYAN}$controller${NC}"
                    done
                fi
            fi
        fi
    fi
}

# 顯示正在運行的評估任務
show_running_evaluations() {
    echo -e "${BLUE}正在運行的評估任務:${NC}"
    echo ""
    
    # 檢查所有 rmfs_ 開頭的 screen 會話（包括新格式）
    sessions=$(screen -ls | grep -E "rmfs_(eval|time_based|queue_based|dqn|nerl)" | wc -l)
    if [ $sessions -eq 0 ]; then
        echo -e "${YELLOW}  無正在運行的評估任務${NC}"
    else
        echo -e "${GREEN}  找到 $sessions 個正在運行的評估任務:${NC}"
        local index=1
        screen -ls | grep -E "rmfs_(eval|time_based|queue_based|dqn|nerl)" | while read line; do
            session_name=$(echo $line | awk '{print $1}')
            
            # 解析會話名稱以獲取資訊
            if [[ "$session_name" == *"rmfs_eval_"* ]]; then
                # 舊格式：單一會話
                session_time=$(echo $session_name | sed 's/.*rmfs_eval_//')
                echo -e "${GREEN}  [$index] $session_name${NC} ${YELLOW}(單一會話模式)${NC}"
                
                eval_dir="result/evaluations/EVAL_${session_time}"
                if [ -d "$eval_dir" ]; then
                    echo -e "${CYAN}      目錄: $eval_dir${NC}"
                fi
            else
                # 新格式：多會話模式
                # 從會話名稱提取模型資訊
                if [[ "$session_name" == *"rmfs_dqn_"* ]]; then
                    model_info=$(echo $session_name | sed 's/.*rmfs_dqn_//' | sed 's/_[0-9]\{8\}_[0-9]\{6\}$//')
                    echo -e "${GREEN}  [$index] $session_name${NC}"
                    echo -e "${PURPLE}      模型: DQN - ${model_info}${NC}"
                elif [[ "$session_name" == *"rmfs_nerl_"* ]]; then
                    model_info=$(echo $session_name | sed 's/.*rmfs_nerl_//' | sed 's/_[0-9]\{8\}_[0-9]\{6\}$//')
                    echo -e "${GREEN}  [$index] $session_name${NC}"
                    echo -e "${PURPLE}      模型: NERL - ${model_info}${NC}"
                elif [[ "$session_name" == *"rmfs_time_based_"* ]]; then
                    echo -e "${GREEN}  [$index] $session_name${NC}"
                    echo -e "${PURPLE}      模型: Time-based Controller${NC}"
                elif [[ "$session_name" == *"rmfs_queue_based_"* ]]; then
                    echo -e "${GREEN}  [$index] $session_name${NC}"
                    echo -e "${PURPLE}      模型: Queue-based Controller${NC}"
                fi
            fi
            
            ((index++))
        done
        
        echo ""
        echo -e "${BLUE}提示:${NC}"
        echo -e "${BLUE}  查看進度: screen -r <session_name>${NC}"
        echo -e "${BLUE}  分離會話: Ctrl+A 然後 D${NC}"
        echo -e "${BLUE}  使用選項 [3] 選擇並連接到特定會話${NC}"
    fi
    echo ""
}

# 快速評估函數
quick_evaluation() {
    local ticks=$1
    local desc=$2
    
    echo -e "${BLUE}執行${desc}...${NC}"
    echo -e "${YELLOW}評估參數: $ticks ticks, 3 次重複${NC}"
    
    # 掃描可用的模型
    scan_available_models > /dev/null
    
    # 選擇所有控制器
    SELECTED_CONTROLLERS=()
    for i in "${!CONTROLLER_SPEC[@]}"; do
        SELECTED_CONTROLLERS+=("${CONTROLLER_SPEC[$i]}")
    done
    
    EVAL_TICKS=$ticks
    NUM_RUNS=3
    PARALLEL_EVAL=true
    
    run_evaluation
}

# 查看運行中的評估
view_running_evaluation() {
    echo -e "${BLUE}選擇要查看的評估任務:${NC}"
    echo ""
    
    # 檢查 screen 會話（包括新舊格式）
    sessions=$(screen -ls | grep -E "rmfs_(eval|time_based|queue_based|dqn|nerl)" | awk '{print $1}')
    if [ -z "$sessions" ]; then
        echo -e "${YELLOW}無正在運行的評估任務${NC}"
        return 1
    fi
    
    # 列出所有評估會話，帶編號
    local index=1
    declare -a session_array
    
    echo "$sessions" | while read session_name; do
        session_array[$index]="$session_name"
        
        # 顯示會話資訊
        echo -e "${CYAN}[$index]${NC} $session_name"
        
        # 根據會話名稱格式顯示不同資訊
        if [[ "$session_name" == *"rmfs_eval_"* ]]; then
            # 舊格式：單一會話模式
            session_time=$(echo "$session_name" | sed 's/.*rmfs_eval_//')
            echo -e "    ${YELLOW}模式: 單一會話（所有模型在此會話中）${NC}"
            
            eval_dir="result/evaluations/EVAL_${session_time}"
            if [ -d "$eval_dir" ]; then
                # 從評估摘要讀取控制器資訊
                if [ -f "$eval_dir/evaluation_summary.json" ]; then
                    echo -e "    ${GREEN}評估目錄: $eval_dir${NC}"
                    if command -v jq &> /dev/null; then
                        controllers=$(jq -r '.controllers_evaluated[]?' "$eval_dir/evaluation_summary.json" 2>/dev/null | head -5)
                        if [ -n "$controllers" ]; then
                            echo -e "    ${GREEN}控制器:${NC}"
                            echo "$controllers" | while read ctrl; do
                                if [[ "$ctrl" == *":"* ]]; then
                                    model_type=$(echo "$ctrl" | cut -d':' -f1)
                                    model_path=$(echo "$ctrl" | cut -d':' -f2-)
                                    model_name=$(basename "$model_path")
                                    echo -e "      • ${CYAN}$model_type${NC}: $model_name"
                                else
                                    echo -e "      • ${CYAN}$ctrl${NC}"
                                fi
                            done
                        fi
                    fi
                fi
            fi
        else
            # 新格式：多會話模式
            echo -e "    ${YELLOW}模式: 獨立會話${NC}"
            
            # 解析模型類型和名稱
            if [[ "$session_name" == *"rmfs_dqn_"* ]]; then
                model_info=$(echo $session_name | sed 's/.*rmfs_dqn_//' | sed 's/_[0-9]\{8\}_[0-9]\{6\}$//')
                echo -e "    ${PURPLE}模型: DQN - ${model_info}.pth${NC}"
            elif [[ "$session_name" == *"rmfs_nerl_"* ]]; then
                model_info=$(echo $session_name | sed 's/.*rmfs_nerl_//' | sed 's/_[0-9]\{8\}_[0-9]\{6\}$//')
                echo -e "    ${PURPLE}模型: NERL - ${model_info}.pth${NC}"
            elif [[ "$session_name" == *"rmfs_time_based_"* ]]; then
                echo -e "    ${PURPLE}模型: Time-based Controller${NC}"
            elif [[ "$session_name" == *"rmfs_queue_based_"* ]]; then
                echo -e "    ${PURPLE}模型: Queue-based Controller${NC}"
            fi
        fi
        
        echo ""
        ((index++))
    done
    
    # 重新掃描以建立陣列（因為 while 在子 shell 中執行）
    index=1
    session_array=()
    while IFS= read -r session_name; do
        session_array[$index]="$session_name"
        ((index++))
    done <<< "$sessions"
    
    echo ""
    echo -e "${YELLOW}選擇要連接的會話編號 (按 Enter 返回主選單):${NC}"
    read -p "請選擇: " choice
    
    if [ -z "$choice" ]; then
        return 0
    fi
    
    if [ -n "${session_array[$choice]}" ]; then
        selected_session="${session_array[$choice]}"
        echo ""
        echo -e "${BLUE}連接到: $selected_session${NC}"
        echo -e "${YELLOW}提示:${NC}"
        echo -e "${YELLOW}  • 按 Ctrl+C 可以中斷評估${NC}"
        echo -e "${YELLOW}  • 按 Ctrl+A 然後 D 可以分離會話（保持運行）${NC}"
        echo -e "${YELLOW}  • 評估完成後按任意鍵退出${NC}"
        echo ""
        echo -e "${GREEN}按任意鍵連接...${NC}"
        read
        
        # 連接到 screen 會話
        screen -r "$selected_session"
    else
        echo -e "${RED}無效的選擇${NC}"
    fi
}

# 停止評估任務
stop_evaluation_task() {
    echo -e "${BLUE}正在運行的評估任務:${NC}"
    
    # 檢查所有 RMFS 相關的 screen 會話（包括新舊格式）
    sessions=$(screen -ls | grep -E "rmfs_(eval|time_based|queue_based|dqn|nerl)" | awk '{print $1}')
    if [ -z "$sessions" ]; then
        echo -e "${YELLOW}  無正在運行的評估任務${NC}"
        return 1
    fi
    
    # 列出所有評估會話
    echo "$sessions" | nl -w3 -s') '
    echo ""
    
    echo -e "${YELLOW}選擇要停止的任務編號，或輸入 'all' 停止所有任務${NC}"
    read -p "請選擇: " choice
    
    if [ "$choice" = "all" ]; then
        # 停止所有評估任務
        echo -e "${RED}確定要停止所有評估任務嗎? (y/N)${NC}"
        read -p "輸入 'y' 確認: " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo "$sessions" | while read session_name; do
                screen -S "$session_name" -X quit
                echo -e "${GREEN}✅ 已停止: $session_name${NC}"
            done
            echo -e "${GREEN}所有評估任務已停止${NC}"
        else
            echo -e "${YELLOW}取消操作${NC}"
        fi
    elif [[ "$choice" =~ ^[0-9]+$ ]]; then
        # 停止特定任務
        session_name=$(echo "$sessions" | sed -n "${choice}p")
        if [ -z "$session_name" ]; then
            echo -e "${RED}無效的選擇${NC}"
            return 1
        fi
        
        echo -e "${RED}確定要停止任務 '$session_name' 嗎? (y/N)${NC}"
        read -p "輸入 'y' 確認: " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            screen -S "$session_name" -X quit
            echo -e "${GREEN}✅ 任務 '$session_name' 已停止${NC}"
        else
            echo -e "${YELLOW}取消操作${NC}"
        fi
    else
        echo -e "${RED}無效的選擇${NC}"
    fi
    
    # 同時檢查是否有 Python 評估進程在運行
    echo ""
    echo -e "${BLUE}檢查 Python 評估進程...${NC}"
    
    eval_procs=$(ps aux | grep "python evaluate.py" | grep -v grep)
    if [ -n "$eval_procs" ]; then
        echo -e "${YELLOW}發現以下 Python 評估進程:${NC}"
        echo "$eval_procs" | while IFS= read -r line; do
            pid=$(echo "$line" | awk '{print $2}')
            cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
            echo -e "  PID: ${CYAN}$pid${NC} - $cmd"
        done
        
        echo ""
        echo -e "${YELLOW}是否要終止這些 Python 進程? (y/N)${NC}"
        read -p "請選擇: " kill_python
        
        if [ "$kill_python" = "y" ] || [ "$kill_python" = "Y" ]; then
            echo "$eval_procs" | while IFS= read -r line; do
                pid=$(echo "$line" | awk '{print $2}')
                kill -15 $pid 2>/dev/null
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}✅ 已終止進程 PID: $pid${NC}"
                else
                    echo -e "${RED}❌ 無法終止進程 PID: $pid (可能需要 sudo 權限)${NC}"
                fi
            done
        fi
    else
        echo -e "${GREEN}沒有發現運行中的 Python 評估進程${NC}"
    fi
}

# 聚合多會話結果
aggregate_multi_session_results() {
    echo -e "${BLUE}多會話結果聚合工具${NC}"
    echo ""
    
    # 查找最近的多會話評估結果
    echo -e "${CYAN}正在尋找多會話評估結果...${NC}"
    
    # 獲取最近修改的評估目錄
    recent_dirs=$(ls -dt result/evaluations/EVAL_* 2>/dev/null | head -20)
    
    if [ -z "$recent_dirs" ]; then
        echo -e "${YELLOW}未找到任何評估結果${NC}"
        return 1
    fi
    
    # 分析目錄，找出屬於同一批次的多會話結果
    declare -A session_groups
    
    for dir in $recent_dirs; do
        if [ -d "$dir" ]; then
            # 提取時間戳（最後 15 個字符）
            dir_name=$(basename "$dir")
            timestamp="${dir_name: -15}"
            
            # 檢查是否為多會話格式
            if [[ "$dir_name" =~ EVAL_(time_based|queue_based|dqn|nerl).*_${timestamp} ]]; then
                session_groups["$timestamp"]+="$dir "
            fi
        fi
    done
    
    # 顯示找到的會話組
    if [ ${#session_groups[@]} -eq 0 ]; then
        echo -e "${YELLOW}未找到多會話評估結果${NC}"
        echo -e "${BLUE}提示：只有使用多會話模式的評估才需要聚合${NC}"
        return 1
    fi
    
    echo -e "${GREEN}找到以下多會話評估批次:${NC}"
    echo ""
    
    local index=1
    declare -a group_keys
    
    for timestamp in "${!session_groups[@]}"; do
        group_keys[$index]="$timestamp"
        echo -e "${CYAN}[$index] 批次時間: $timestamp${NC}"
        
        # 顯示該批次的控制器
        for dir in ${session_groups[$timestamp]}; do
            controller=$(basename "$dir" | sed -E "s/EVAL_(.*)_${timestamp}/\1/")
            echo -e "      • $controller"
        done
        
        ((index++))
        echo ""
    done
    
    echo -e "${YELLOW}請選擇要聚合的批次 [1-$((index-1))]，或輸入 0 取消:${NC}"
    read -p "請選擇: " choice
    
    if [ "$choice" = "0" ]; then
        echo -e "${YELLOW}已取消${NC}"
        return 0
    fi
    
    if [ "$choice" -lt 1 ] || [ "$choice" -ge "$index" ]; then
        echo -e "${RED}無效的選擇${NC}"
        return 1
    fi
    
    # 獲取選中的時間戳和目錄
    selected_timestamp="${group_keys[$choice]}"
    selected_dirs="${session_groups[$selected_timestamp]}"
    
    echo ""
    echo -e "${GREEN}準備聚合以下目錄:${NC}"
    for dir in $selected_dirs; do
        echo -e "  • $dir"
    done
    
    # 詢問輸出目錄
    echo ""
    echo -e "${BLUE}輸出目錄選項:${NC}"
    echo "  [1] 使用第一個評估目錄（預設）"
    echo "  [2] 創建新的聚合目錄"
    
    read -p "請選擇 [1-2]: " output_choice
    
    output_dir=""
    if [ "$output_choice" = "2" ]; then
        output_dir="result/evaluations/AGGREGATED_${selected_timestamp}"
        mkdir -p "$output_dir"
        echo -e "${GREEN}將輸出到: $output_dir${NC}"
    fi
    
    # 執行聚合
    echo ""
    echo -e "${CYAN}開始聚合...${NC}"
    
    # 構建命令
    aggregate_cmd="python aggregate_results.py"
    
    # 添加所有目錄
    for dir in $selected_dirs; do
        aggregate_cmd="$aggregate_cmd $dir"
    done
    
    # 添加輸出目錄（如果指定）
    if [ -n "$output_dir" ]; then
        aggregate_cmd="$aggregate_cmd --output $output_dir"
    fi
    
    echo -e "${YELLOW}執行命令: $aggregate_cmd${NC}"
    echo ""
    
    # 執行聚合
    $aggregate_cmd
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ 聚合完成！${NC}"
        
        # 顯示生成的文件
        if [ -n "$output_dir" ]; then
            target_dir="$output_dir"
        else
            target_dir=$(echo $selected_dirs | awk '{print $1}')
        fi
        
        echo -e "${BLUE}生成的文件:${NC}"
        ls -la "$target_dir"/aggregated_* 2>/dev/null | while read line; do
            echo "  $line"
        done
    else
        echo -e "${RED}❌ 聚合失敗${NC}"
    fi
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
    echo -e "${YELLOW}任務管理:${NC}"
    echo "  [7] 停止正在運行的評估"
    echo "  [8] 聚合多會話結果（生成比較圖表）"
    echo ""
    echo -e "${RED}其他選項:${NC}"
    echo "  [0] 離開"
    echo ""
    echo -e "${BLUE}================================================================${NC}"
}

# 主迴圈
main() {
    while true; do
        show_header
        show_system_status
        show_running_evaluations
        show_main_menu
        
        read -p "請選擇 [0-8]: " choice
        
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
                # 查看正在運行的評估
                view_running_evaluation
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
            7)
                # 停止評估任務
                stop_evaluation_task
                ;;
            8)
                # 聚合多會話結果
                aggregate_multi_session_results
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