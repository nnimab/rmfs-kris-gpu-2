#!/bin/bash
# RMFS 背景測試執行腳本

# 設定測試參數
ROBOT_COUNTS="20,25,30"  # 機器人數量
RUNS_PER_CONFIG=4        # 每個配置運行次數
TEST_TICKS=20000         # 測試 ticks
PARALLEL=true            # 並行執行
MAX_PARALLEL=8           # 最大並行數

# 創建日誌目錄
LOG_DIR="test/background_logs"
mkdir -p "$LOG_DIR"

# 生成時間戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/test_${TIMESTAMP}.log"

echo "開始背景測試 - $(date)" | tee "$LOG_FILE"
echo "機器人數量: $ROBOT_COUNTS" | tee -a "$LOG_FILE"
echo "每個配置運行: $RUNS_PER_CONFIG 次" | tee -a "$LOG_FILE"
echo "測試 ticks: $TEST_TICKS" | tee -a "$LOG_FILE"
echo "日誌檔案: $LOG_FILE" | tee -a "$LOG_FILE"

# 使用 nohup 在背景執行
nohup python -u test/capacity_test_controller.py \
    --robot-counts $ROBOT_COUNTS \
    --ticks $TEST_TICKS \
    --parallel \
    --max-parallel $MAX_PARALLEL \
    >> "$LOG_FILE" 2>&1 &

# 獲取進程 ID
PID=$!
echo "進程 ID: $PID" | tee -a "$LOG_FILE"

# 保存進程資訊
echo "$PID" > "$LOG_DIR/test_${TIMESTAMP}.pid"

echo "測試已在背景開始執行！"
echo "查看進度: tail -f $LOG_FILE"
echo "檢查進程: ps -p $PID"
echo "停止測試: kill $PID"