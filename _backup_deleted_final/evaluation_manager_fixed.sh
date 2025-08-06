#!/bin/bash
# 修正版片段 - 檢查是否已有 SIMULATION_ID

# 在設定 SIMULATION_ID 之前檢查
if [ -z "$SIMULATION_ID" ]; then
    # 如果沒有設定，使用自動生成的
    export SIMULATION_ID="batch_${base_timestamp}_run${run_num}"
    echo "使用自動生成的 SIMULATION_ID: $SIMULATION_ID"
else
    # 如果已經設定，保留原值
    echo "使用預設的 SIMULATION_ID: $SIMULATION_ID"
fi

# 在 screen 會話中也要傳遞
screen -dmS "$screen_name" bash -c "
    cd $PROJECT_DIR
    source .venv/bin/activate
    export PYTHONPATH=$PROJECT_DIR:\$PYTHONPATH
    export SIMULATION_ID='$SIMULATION_ID'  # 使用變數而非寫死
    
    echo 'SIMULATION_ID: '\$SIMULATION_ID
    # ... 其他命令
"