#!/bin/bash

# RMFS 專案快速啟動腳本
echo "=================================================="
echo "  RMFS 倉儲自動化研究專案"
echo "  Neural Evolution Reinforcement Learning"
echo "=================================================="

# 進入專案目錄
cd /workspace/rmfs-kris-gpu-1

# 設定Python路徑
export PYTHONPATH=/workspace/rmfs-kris-gpu-1:$PYTHONPATH

# 顯示當前狀態
echo "✅ 已進入專案目錄: $(pwd)"
echo "✅ Python路徑已設定: $PYTHONPATH"

# 檢查GPU狀態
if command -v nvidia-smi &> /dev/null; then
    echo "✅ GPU 狀態:"
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits | head -1
else
    echo "⚠️  GPU 未檢測到"
fi

echo ""
echo "常用命令:"
echo "  python train.py --agent dqn --episodes 10 --ticks 1000"
echo "  python evaluate.py --ticks 5000 --seed 42"
echo "  python simple_experiment.py"
echo "  python check_system.py"
echo ""
echo "準備就緒！可以開始實驗了 🚀"
echo "=================================================="