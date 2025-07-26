#!/bin/bash

# 修改版：支援 SIMULATION_ID 的並行評估腳本

# 原有的設定
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}並行評估啟動器${NC}"
echo ""

# 並行執行多個評估
run_parallel_evaluations() {
    local controllers=("$@")
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    echo -e "${GREEN}將並行執行 ${#controllers[@]} 個評估${NC}"
    
    for i in "${!controllers[@]}"; do
        controller="${controllers[$i]}"
        sim_id="eval_${timestamp}_${i}"
        
        echo -e "${YELLOW}啟動評估 $((i+1)): $controller${NC}"
        
        # 創建 screen 會話，設定 SIMULATION_ID
        screen -dmS "rmfs_${sim_id}" bash -c "
            export SIMULATION_ID='${sim_id}'
            export PYTHONPATH='$PROJECT_DIR:\$PYTHONPATH'
            source .venv/bin/activate
            
            echo '開始評估: $controller'
            echo 'SIMULATION_ID: ${sim_id}'
            echo '狀態檔案: states/netlogo_${sim_id}.state'
            
            python evaluate.py --controllers $controller --eval_ticks 20000 --num_runs 1
            
            echo ''
            echo '評估完成！按任意鍵結束...'
            read
        "
        
        # 延遲啟動下一個
        if [ $((i+1)) -lt ${#controllers[@]} ]; then
            echo "等待 5 秒再啟動下一個..."
            sleep 5
        fi
    done
    
    echo ""
    echo -e "${GREEN}所有評估已啟動！${NC}"
    echo ""
    echo "使用以下命令查看狀態："
    echo "  screen -ls          # 列出所有會話"
    echo "  screen -r rmfs_XXX  # 連接到特定會話"
    echo ""
    echo "狀態檔案位於 states/ 目錄"
}

# 主程式
echo "選擇要並行評估的控制器："
echo "  1) time_based + queue_based"
echo "  2) time_based + none"
echo "  3) 所有傳統控制器"
echo "  4) 自定義"
echo ""
read -p "請選擇 [1-4]: " choice

case $choice in
    1)
        run_parallel_evaluations "time_based" "queue_based"
        ;;
    2)
        run_parallel_evaluations "time_based" "none"
        ;;
    3)
        run_parallel_evaluations "time_based" "queue_based" "none"
        ;;
    4)
        echo "輸入控制器列表（空格分隔）："
        read -a custom_controllers
        run_parallel_evaluations "${custom_controllers[@]}"
        ;;
    *)
        echo "無效選擇"
        exit 1
        ;;
esac