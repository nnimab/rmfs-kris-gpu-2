#!/bin/bash
# 執行多run容量測試的腳本

echo "======================================"
echo "執行多run容量測試"
echo "======================================"

# 確保在專案根目錄執行
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 執行測試
python test/test_multi_run.py

# 檢查執行結果
if [ $? -eq 0 ]; then
    echo -e "\n✅ 測試完成"
else
    echo -e "\n❌ 測試失敗"
    exit 1
fi