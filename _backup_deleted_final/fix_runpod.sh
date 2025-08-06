#!/bin/bash
# RunPod 快速修復腳本

echo "修復 RunPod 上的 evaluate.py..."

# 備份原始檔案
cp evaluate.py evaluate.py.backup

# 修復 Robot.path 錯誤
sed -i 's/if len(r\.path) > 0/if hasattr(r, "route_stop_points") and len(r.route_stop_points) > 0/g' evaluate.py

# 修復其他已知問題
sed -i 's/r\.total_wait_time/sum(r.intersection_wait_time.values()) if hasattr(r, "intersection_wait_time") else 0/g' evaluate.py
sed -i 's/r\.energy_consumed/r.energy_consumption if hasattr(r, "energy_consumption") else 0/g' evaluate.py

echo "修復完成！"
echo "檢查修改："
grep -n "route_stop_points" evaluate.py