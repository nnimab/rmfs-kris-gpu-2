#!/bin/bash
# 執行監控功能演示

echo "======================================"
echo "RMFS 容量測試監控功能演示"
echo "======================================"

# 確保在專案根目錄執行
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 選項選單
echo ""
echo "請選擇要執行的演示："
echo "1. 監控UI靜態演示"
echo "2. 背景執行測試（實際運行）"
echo "3. 完整選單系統"
echo ""

read -p "請輸入選項 (1-3): " choice

case $choice in
    1)
        echo "執行監控UI演示..."
        python test/demo_monitor_ui.py
        ;;
    2)
        echo "執行背景測試..."
        python test/test_background_monitor.py
        ;;
    3)
        echo "啟動完整選單系統..."
        python test/experiment_menu.py
        ;;
    *)
        echo "無效選項"
        exit 1
        ;;
esac