#!/bin/bash

# RMFS 訓練管理器 - 支援後台持續訓練
# 使用 screen 保持訓練進程在 SSH 斷線後繼續運行

# 設定顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案目錄 (自動偵測)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 自動設置虛擬環境
setup_environment() {
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}創建虛擬環境...${NC}"
        python3.11 -m venv .venv
    fi
    
    echo -e "${GREEN}啟動虛擬環境...${NC}"
    source .venv/bin/activate
    
    # 檢查是否需要安裝套件
    if ! python -c "import torch; print('PyTorch 已安裝')" 2>/dev/null; then
        echo -e "${YELLOW}安裝 PyTorch (GPU版本)...${NC}"
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
        
        echo -e "${YELLOW}安裝其他依賴套件...${NC}"
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
    echo -e "${BLUE}              RMFS 訓練管理器 (後台持續訓練)${NC}"
    echo -e "${BLUE}          Neural Evolution Reinforcement Learning${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

# 顯示系統狀態
show_system_status() {
    echo -e "${GREEN}✅ 專案目錄: ${NC}$(pwd)"
    echo -e "${GREEN}✅ Python路徑: ${NC}$PYTHONPATH"
    
    # 檢查GPU狀態
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✅ GPU 狀態: ${NC}"
        nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits | head -1
    else
        echo -e "${YELLOW}⚠️  GPU 未檢測到${NC}"
    fi
    echo ""
}

# 顯示正在運行的訓練任務
show_running_tasks() {
    echo -e "${BLUE}正在運行的訓練任務:${NC}"
    
    # 檢查 screen 會話
    sessions=$(screen -ls | grep "rmfs_train" | wc -l)
    if [ $sessions -eq 0 ]; then
        echo -e "${YELLOW}  無正在運行的訓練任務${NC}"
    else
        echo -e "${GREEN}  找到 $sessions 個正在運行的訓練任務:${NC}"
        screen -ls | grep "rmfs_train" | while read line; do
            session_name=$(echo $line | awk '{print $1}')
            echo -e "${GREEN}    - $session_name${NC}"
        done
    fi
    echo ""
}

# 啟動訓練任務
start_training() {
    local task_name=$1
    local command=$2
    local screen_name="rmfs_train_$task_name"
    
    # 檢查是否已存在同名會話
    if screen -list | grep -q "$screen_name"; then
        echo -e "${RED}錯誤: 訓練任務 '$task_name' 已經在運行中${NC}"
        echo -e "${YELLOW}請先終止現有任務或選擇其他任務名稱${NC}"
        return 1
    fi
    
    echo -e "${BLUE}啟動訓練任務: $task_name${NC}"
    echo -e "${BLUE}執行命令: $command${NC}"
    echo -e "${BLUE}Screen 會話: $screen_name${NC}"
    echo ""
    
    # 創建 screen 會話並執行命令
    screen -dmS "$screen_name" bash -c "
        cd $PROJECT_DIR
        
        # 在 screen 中也啟動虛擬環境
        if [ -d '.venv' ]; then
            source .venv/bin/activate
            echo '✅ 虛擬環境已啟動'
        fi
        
        export PYTHONPATH=$PROJECT_DIR:\$PYTHONPATH
        echo '開始訓練任務: $task_name'
        echo '時間: \$(date)'
        echo '命令: $command'
        echo '================================='
        $command
        echo '================================='
        echo '訓練任務完成: $task_name'
        echo '結束時間: \$(date)'
        echo '按任意鍵結束...'
        read
    "
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 訓練任務 '$task_name' 已在後台啟動${NC}"
        echo -e "${GREEN}✅ 即使關閉 SSH 連線，訓練也會繼續運行${NC}"
        echo -e "${BLUE}💡 使用選項 '4' 來查看任務輸出${NC}"
        echo -e "${BLUE}💡 使用選項 '5' 來終止任務${NC}"
    else
        echo -e "${RED}❌ 啟動訓練任務失敗${NC}"
    fi
}

# 查看任務輸出
view_task_output() {
    echo -e "${BLUE}可用的訓練任務:${NC}"
    
    # 列出所有 rmfs_train 會話
    sessions=$(screen -ls | grep "rmfs_train" | awk '{print $1}')
    if [ -z "$sessions" ]; then
        echo -e "${YELLOW}  無正在運行的訓練任務${NC}"
        return 1
    fi
    
    echo "$sessions" | nl -w3 -s') '
    echo ""
    
    read -p "選擇要查看的任務編號 (按 Enter 取消): " choice
    if [ -z "$choice" ]; then
        return 0
    fi
    
    session_name=$(echo "$sessions" | sed -n "${choice}p")
    if [ -z "$session_name" ]; then
        echo -e "${RED}無效的選擇${NC}"
        return 1
    fi
    
    echo -e "${BLUE}連接到任務: $session_name${NC}"
    echo -e "${YELLOW}按 Ctrl+A 然後 D 來離開但保持任務運行${NC}"
    echo -e "${YELLOW}按任意鍵繼續...${NC}"
    read
    
    # 連接到 screen 會話
    screen -r "$session_name"
}

# 終止訓練任務
kill_training_task() {
    echo -e "${BLUE}正在運行的訓練任務:${NC}"
    
    # 列出所有 rmfs_train 會話
    sessions=$(screen -ls | grep "rmfs_train" | awk '{print $1}')
    if [ -z "$sessions" ]; then
        echo -e "${YELLOW}  無正在運行的訓練任務${NC}"
        return 1
    fi
    
    echo "$sessions" | nl -w3 -s') '
    echo ""
    
    read -p "選擇要終止的任務編號 (按 Enter 取消): " choice
    if [ -z "$choice" ]; then
        return 0
    fi
    
    session_name=$(echo "$sessions" | sed -n "${choice}p")
    if [ -z "$session_name" ]; then
        echo -e "${RED}無效的選擇${NC}"
        return 1
    fi
    
    echo -e "${RED}確定要終止任務 '$session_name' 嗎? (y/N)${NC}"
    read -p "輸入 'y' 確認: " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        screen -S "$session_name" -X quit
        echo -e "${GREEN}✅ 任務 '$session_name' 已終止${NC}"
    else
        echo -e "${YELLOW}取消終止任務${NC}"
    fi
}

# 顯示系統資源使用情況
show_resource_usage() {
    clear
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}                    系統資源使用情況${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    
    # CPU 使用率
    echo -e "${GREEN}🖥️  CPU 使用率:${NC}"
    cpu_usage=$(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)
    echo "    使用率: ${cpu_usage}%"
    echo ""
    
    # 記憶體使用情況
    echo -e "${GREEN}💾 記憶體使用情況:${NC}"
    mem_info=$(free -h | grep Mem)
    mem_total=$(echo $mem_info | awk '{print $2}')
    mem_used=$(echo $mem_info | awk '{print $3}')
    mem_avail=$(echo $mem_info | awk '{print $7}')
    echo "    總記憶體: $mem_total"
    echo "    已使用: $mem_used"
    echo "    可用: $mem_avail"
    
    swap_info=$(free -h | grep Swap)
    swap_total=$(echo $swap_info | awk '{print $2}')
    swap_used=$(echo $swap_info | awk '{print $3}')
    echo "    Swap: $swap_used / $swap_total"
    echo ""
    
    # GPU 使用情況
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}🚀 GPU 使用情況:${NC}"
        nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | \
        while IFS=',' read -r index name gpu_util mem_used mem_total temp; do
            name=$(echo "$name" | xargs)
            gpu_util=$(echo "$gpu_util" | xargs)
            mem_used=$(echo "$mem_used" | xargs)
            mem_total=$(echo "$mem_total" | xargs)
            temp=$(echo "$temp" | xargs)
            
            echo "    GPU $index: $name"
            echo "      使用率: ${gpu_util}%"
            echo "      記憶體: ${mem_used}MB / ${mem_total}MB ($(( mem_used * 100 / mem_total ))%)"
            echo "      溫度: ${temp}°C"
            echo ""
        done
    else
        echo -e "${YELLOW}⚠️  未檢測到 GPU${NC}"
    fi
    
    # 硬碟使用情況
    echo -e "${GREEN}💿 硬碟使用情況:${NC}"
    df -h | grep -E "/$|/workspace" | while read line; do
        filesystem=$(echo $line | awk '{print $1}')
        size=$(echo $line | awk '{print $2}')
        used=$(echo $line | awk '{print $3}')
        avail=$(echo $line | awk '{print $4}')
        use_percent=$(echo $line | awk '{print $5}')
        mount=$(echo $line | awk '{print $6}')
        echo "    $mount: $used / $size ($use_percent 使用)"
    done
    echo ""
    
    # 執行中的 Python 訓練程序
    echo -e "${GREEN}🐍 執行中的 Python 訓練程序:${NC}"
    
    # 只顯示主要的 train.py 程序，不顯示多進程的子程序
    main_train_procs=$(ps aux | grep "python train.py" | grep -v grep)
    worker_procs=$(ps aux | grep "multiprocessing.spawn import spawn_main" | grep -v grep | wc -l)
    
    if [ -z "$main_train_procs" ]; then
        echo "    無訓練程序正在運行"
    else
        echo "$main_train_procs" | while IFS= read -r line; do
            pid=$(echo "$line" | awk '{print $2}')
            cpu=$(echo "$line" | awk '{print $3}')
            mem=$(echo "$line" | awk '{print $4}')
            
            # 解析參數
            agent_type=$(echo "$line" | grep -o -- "--agent [a-z]*" | awk '{print $2}')
            reward_mode=$(echo "$line" | grep -o -- "--reward_mode [a-z]*" | awk '{print $2}')
            variant=$(echo "$line" | grep -o -- "--variant [a-z]*" | awk '{print $2}')
            
            # 組合任務名稱
            task_name="${agent_type}"
            if [ -n "$reward_mode" ]; then
                task_name="${task_name}_${reward_mode}"
            fi
            if [ -n "$variant" ]; then
                task_name="${task_name}_${variant}"
            fi
            
            echo "    PID: $pid | CPU: ${cpu}% | MEM: ${mem}% | 訓練任務: ${task_name}"
        done
        
        # 顯示並行 worker 數量
        if [ $worker_procs -gt 0 ]; then
            echo "    並行 Workers: $worker_procs 個子程序"
        fi
    fi
    echo ""
    
    # 系統負載
    echo -e "${GREEN}⚡ 系統負載:${NC}"
    load_info=$(uptime | awk -F'load average:' '{print $2}')
    echo "    負載平均: $load_info"
    echo ""
    
    # 建議的並行任務數
    echo -e "${BLUE}💡 建議的並行任務數:${NC}"
    
    # 獲取實際的資源限制
    cpu_cores=$(nproc)
    cpu_quota=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo "-1")
    cpu_period=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo "100000")
    
    if [ "$cpu_quota" != "-1" ]; then
        actual_cpu_cores=$(awk "BEGIN {printf \"%.1f\", $cpu_quota/$cpu_period}")
        echo "    顯示的 CPU 核心: $cpu_cores (虛擬)"
        echo "    實際可用 CPU 核心: $actual_cpu_cores"
    else
        actual_cpu_cores=$cpu_cores
        echo "    CPU 核心數: $cpu_cores"
    fi
    
    # 獲取記憶體限制
    mem_limit=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo "0")
    total_mem=$(free -g | grep Mem | awk '{print $2}')
    
    if [ "$mem_limit" != "0" ] && [ "$mem_limit" -lt "9223372036854775807" ]; then
        actual_mem=$(awk "BEGIN {printf \"%.0f\", $mem_limit/1024/1024/1024}")
        echo "    顯示的記憶體: ${total_mem}GB (系統總量)"
        echo "    實際可用記憶體: ${actual_mem}GB"
    else
        actual_mem=$total_mem
        echo "    記憶體: ${total_mem}GB"
    fi
    
    gpu_count=$(nvidia-smi --list-gpus 2>/dev/null | wc -l)
    current_load=$(uptime | awk '{print $(NF-2)}' | sed 's/,//')
    
    echo "    GPU 數量: $gpu_count"
    echo "    目前負載: $current_load"
    echo ""
    
    # 根據系統狀態動態調整建議
    load_threshold=$(awk "BEGIN {printf \"%.1f\", $actual_cpu_cores * 1.5}")
    running_tasks=$(screen -ls | grep "rmfs_train" | wc -l)
    gpu_mem_used_percent=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F, '{print int($1*100/$2)}')
    
    echo ""
    echo -e "${BLUE}    📊 當前系統狀態分析:${NC}"
    echo "       • 已運行訓練任務: $running_tasks 個"
    echo "       • GPU 記憶體使用率: ${gpu_mem_used_percent}%"
    echo "       • 系統負載: $current_load (建議 < $load_threshold)"
    echo ""
    
    # 更精確的建議邏輯
    if (( $(echo "$current_load > $load_threshold" | awk '{print ($1 > $2)}') )); then
        echo -e "${RED}    ⚠️  CPU 負載過高 (${current_load} > ${load_threshold})${NC}"
        echo -e "${RED}       建議等待現有任務完成或減少 parallel_workers${NC}"
    elif [ $gpu_mem_used_percent -gt 80 ]; then
        echo -e "${RED}    ⚠️  GPU 記憶體使用率過高 (${gpu_mem_used_percent}%)${NC}"
        echo -e "${RED}       建議等待 GPU 記憶體釋放後再啟動新任務${NC}"
    elif [ $running_tasks -ge 2 ]; then
        echo -e "${YELLOW}    ⚡ 已有 $running_tasks 個任務運行中${NC}"
        echo -e "${YELLOW}       建議監控系統資源，謹慎添加新任務${NC}"
    else
        echo -e "${GREEN}    ✅ RunPod 配置 (實際: ${actual_cpu_cores} vCPU, ${actual_mem}GB RAM, RTX 4090)${NC}"
        if (( $(echo "$actual_cpu_cores < 15" | awk '{print ($1 < $2)}') )); then
            echo -e "${YELLOW}       CPU 限制較嚴格，建議:${NC}"
            echo -e "${YELLOW}       • 1 個 NERL 任務 (降低 parallel_workers 到 8-10)${NC}"
            echo -e "${YELLOW}       • 或 1-2 個 DQN 任務${NC}"
        else
            echo -e "${GREEN}       建議: 可同時運行 1-2 個 NERL 任務 或 2-3 個 DQN 任務${NC}"
        fi
        echo -e "${BLUE}       💡 GPU 使用率偏低，可考慮增加網路大小或批次大小${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${YELLOW}按任意鍵返回主選單...${NC}"
    read
}

# 顯示主選單
show_main_menu() {
    echo -e "${BLUE}=== 主選單 ===${NC}"
    echo ""
    echo -e "${GREEN}訓練任務選項:${NC}"
    echo "  [1] DQN Step Reward (1.6M Ticks)"
    echo "  [2] DQN Global Reward (1.6M Ticks)"
    echo "  [3] NERL Step Reward A (20 workers)"
    echo "  [4] NERL Global Reward A (20 workers)"
    echo "  [5] NERL Step Reward B (20 workers)"
    echo "  [6] NERL Global Reward B (20 workers)"
    echo ""
    echo -e "${BLUE}任務管理選項:${NC}"
    echo "  [7] 查看任務輸出"
    echo "  [8] 終止訓練任務"
    echo "  [9] 重新整理狀態"
    echo ""
    echo -e "${YELLOW}分析和評估選項:${NC}"
    echo "  [a] 生成訓練結果圖表"
    echo "  [e] 運行控制器性能評估"
    echo "  [r] 查看系統資源使用情況"
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
        show_running_tasks
        show_main_menu
        
        read -p "請選擇 [0-9/r]: " choice
        
        case $choice in
            1)
                start_training "dqn_step" "python train.py --agent dqn --reward_mode step --log_level DEBUG --training_ticks 1600000"
                ;;
            2)
                start_training "dqn_global" "python train.py --agent dqn --reward_mode global --log_level DEBUG --training_ticks 1600000"
                ;;
            3)
                start_training "nerl_step_a" "python train.py --agent nerl --reward_mode step --log_level DEBUG --variant a --generations 40 --population 10 --eval_ticks 4000 --parallel_workers 12"
                ;;
            4)
                start_training "nerl_global_a" "python train.py --agent nerl --reward_mode global --log_level DEBUG --variant a --generations 40 --population 10 --eval_ticks 4000 --parallel_workers 12"
                ;;
            5)
                start_training "nerl_step_b" "python train.py --agent nerl --reward_mode step --log_level DEBUG --variant b --generations 40 --population 10 --eval_ticks 4000 --parallel_workers 12"
                ;;
            6)
                start_training "nerl_global_b" "python train.py --agent nerl --reward_mode global --log_level DEBUG --variant b --generations 40 --population 10 --eval_ticks 4000 --parallel_workers 12"
                ;;
            7)
                view_task_output
                ;;
            8)
                kill_training_task
                ;;
            9)
                # 重新整理狀態 - 直接繼續迴圈
                ;;
            a|A)
                generate_analysis_charts
                ;;
            e|E)
                run_controller_evaluation
                ;;
            r|R)
                show_resource_usage
                ;;
            0)
                echo -e "${GREEN}感謝使用 RMFS 訓練管理器！${NC}"
                echo -e "${BLUE}注意: 正在運行的訓練任務將繼續在後台執行${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}無效的選擇，請重新輸入${NC}"
                ;;
        esac
        
        if [ "$choice" != "7" ] && [ "$choice" != "9" ] && [ "$choice" != "r" ] && [ "$choice" != "R" ]; then
            echo ""
            echo -e "${YELLOW}按任意鍵繼續...${NC}"
            read
        fi
    done
}

# 生成分析圖表
generate_analysis_charts() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}                    生成訓練結果分析圖表${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    
    echo -e "${GREEN}正在分析訓練結果並生成圖表...${NC}"
    
    # 檢查是否有訓練結果
    if [ ! -d "models/training_runs" ] || [ -z "$(ls -A models/training_runs 2>/dev/null)" ]; then
        echo -e "${RED}❌ 未找到訓練結果目錄或目錄為空${NC}"
        echo -e "${YELLOW}請先完成至少一個訓練任務${NC}"
        return 1
    fi
    
    # 檢查必要的Python套件
    if ! python -c "import matplotlib, pandas, seaborn" 2>/dev/null; then
        echo -e "${YELLOW}安裝可視化套件...${NC}"
        pip install matplotlib pandas seaborn
    fi
    
    # 運行可視化腳本
    python visualization_generator.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ 圖表生成完成！${NC}"
        echo -e "${BLUE}結果保存在 analysis_results/ 目錄中${NC}"
        
        # 列出生成的文件
        if [ -d "analysis_results" ]; then
            echo -e "${GREEN}生成的文件:${NC}"
            ls -la analysis_results/ | grep -E "\.(png|txt)$" | while read line; do
                filename=$(echo $line | awk '{print $9}')
                filesize=$(echo $line | awk '{print $5}')
                echo -e "${GREEN}  • $filename (${filesize} bytes)${NC}"
            done
        fi
    else
        echo -e "${RED}❌ 圖表生成失敗${NC}"
        echo -e "${YELLOW}請檢查訓練結果數據是否完整${NC}"
    fi
}

# 運行控制器性能評估
run_controller_evaluation() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}                    控制器性能評估${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    
    echo -e "${YELLOW}這將比較所有訓練好的控制器與傳統控制器的性能${NC}"
    echo -e "${YELLOW}評估可能需要 30-60 分鐘，建議在後台運行${NC}"
    echo ""
    
    read -p "是否要開始評估？[y/N]: " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "${YELLOW}取消評估${NC}"
        return 0
    fi
    
    # 詢問評估參數
    echo ""
    echo -e "${BLUE}評估參數設置:${NC}"
    read -p "評估時長 (ticks, 預設 5000): " eval_ticks
    eval_ticks=${eval_ticks:-5000}
    
    read -p "重複運行次數 (預設 3): " num_runs
    num_runs=${num_runs:-3}
    
    read -p "是否在後台運行評估？[Y/n]: " background
    background=${background:-y}
    
    # 構建評估命令
    eval_command="python evaluate.py --eval_ticks $eval_ticks --num_runs $num_runs"
    
    if [ "$background" = "y" ] || [ "$background" = "Y" ]; then
        # 後台運行評估
        screen_name="rmfs_evaluation_$(date +%H%M%S)"
        
        screen -dmS "$screen_name" bash -c "
            cd $PROJECT_DIR
            
            if [ -d '.venv' ]; then
                source .venv/bin/activate
                echo '✅ 虛擬環境已啟動'
            fi
            
            export PYTHONPATH=$PROJECT_DIR:\$PYTHONPATH
            echo '開始控制器性能評估'
            echo '時間: \$(date)'
            echo '評估參數: $eval_ticks ticks, $num_runs 次重複'
            echo '================================='
            $eval_command
            echo '================================='
            echo '評估完成時間: \$(date)'
            echo '按任意鍵結束...'
            read
        "
        
        echo -e "${GREEN}✅ 評估任務已在後台啟動 (Screen: $screen_name)${NC}"
        echo -e "${BLUE}💡 使用選項 '7' 來查看評估進度${NC}"
        echo -e "${BLUE}💡 結果將保存在 evaluation_results/ 目錄中${NC}"
    else
        # 前台運行評估
        echo -e "${GREEN}開始前台評估...${NC}"
        $eval_command
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 評估完成！${NC}"
            echo -e "${BLUE}結果保存在 evaluation_results/ 目錄中${NC}"
        else
            echo -e "${RED}❌ 評估失敗${NC}"
        fi
    fi
}

# 檢查 screen 是否安裝
if ! command -v screen &> /dev/null; then
    echo -e "${RED}錯誤: 未安裝 screen 工具${NC}"
    echo -e "${YELLOW}請執行: apt-get install screen${NC}"
    exit 1
fi

# 啟動主程式
main