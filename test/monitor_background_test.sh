#!/bin/bash
# 監控背景測試腳本

LOG_DIR="test/background_logs"

# 檢查是否有執行中的測試
echo "=== 執行中的測試 ==="
for pid_file in "$LOG_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null; then
            echo "進程 $PID 執行中"
            echo "日誌: ${pid_file%.pid}.log"
        else
            echo "進程 $PID 已結束"
            rm "$pid_file"
        fi
    fi
done

echo ""
echo "=== 最新日誌 ==="
LATEST_LOG=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "檢視: tail -f $LATEST_LOG"
    tail -20 "$LATEST_LOG"
else
    echo "沒有找到日誌檔案"
fi