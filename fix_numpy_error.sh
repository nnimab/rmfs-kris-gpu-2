#!/bin/bash

# RunPod NumPy 修復腳本
# 解決 "PyCapsule_Import could not import module datetime" 錯誤

echo "========================================="
echo "開始修復 NumPy 相容性問題..."
echo "========================================="

# 顯示當前環境資訊
echo "1. 檢查當前 Python 和 NumPy 版本..."
python --version
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')" 2>/dev/null || echo "NumPy 尚未正確安裝"

# 方法 1: 升級 pip 並重新安裝 numpy
echo ""
echo "2. 方法 1: 升級 pip 並重新安裝 numpy..."
python -m pip install --upgrade pip
python -m pip uninstall -y numpy
python -m pip install numpy==1.23.5  # 使用與 Python 3.10 相容的版本

# 測試是否修復
echo ""
echo "3. 測試 NumPy 是否正常運作..."
python -c "import numpy; print('NumPy 導入成功！版本:', numpy.__version__)" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "方法 1 失敗，嘗試方法 2..."
    
    # 方法 2: 使用系統套件管理器
    echo ""
    echo "4. 方法 2: 使用 apt 安裝 numpy..."
    apt update
    apt install -y python3-numpy python3-pip
    
    # 再次測試
    python3 -c "import numpy; print('NumPy 導入成功！版本:', numpy.__version__)" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "方法 2 失敗，嘗試方法 3..."
        
        # 方法 3: 完全重新安裝
        echo ""
        echo "5. 方法 3: 完全重新安裝 Python 套件..."
        
        # 清理舊的安裝
        python -m pip uninstall -y numpy scipy pandas matplotlib
        
        # 安裝相容版本
        python -m pip install --no-cache-dir numpy==1.23.5
        python -m pip install --no-cache-dir scipy pandas matplotlib
    fi
fi

# 安裝專案所需的其他套件
echo ""
echo "6. 安裝專案所需套件..."
if [ -f "requirements.txt" ]; then
    # 先安裝相容的 numpy 版本
    python -m pip install numpy==1.23.5
    # 然後安裝其他套件（忽略 numpy 版本衝突）
    python -m pip install -r requirements.txt --upgrade-strategy only-if-needed
else
    echo "未找到 requirements.txt，跳過套件安裝"
fi

# 最終測試
echo ""
echo "========================================="
echo "7. 最終測試..."
python -c "
import sys
print(f'Python: {sys.version}')
try:
    import numpy
    print(f'NumPy: {numpy.__version__} - 導入成功！')
    
    # 測試基本功能
    arr = numpy.array([1, 2, 3])
    print(f'測試陣列: {arr}')
    print('NumPy 功能正常！')
except Exception as e:
    print(f'錯誤: {e}')
"

echo "========================================="
echo "修復腳本執行完成！"
echo ""
echo "如果問題仍然存在，請嘗試："
echo "1. 使用 python3 而不是 python"
echo "2. 創建虛擬環境："
echo "   python -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "========================================="

# 創建一個包裝腳本來確保使用正確的 Python
cat > run_experiment_safe.sh << 'EOF'
#!/bin/bash
# 安全執行實驗的包裝腳本

# 確保使用 UTF-8 編碼
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8
export PYTHONIOENCODING=utf-8

# 嘗試不同的 Python 執行方式
if python3 -c "import numpy" 2>/dev/null; then
    echo "使用 python3 執行..."
    python3 test/experiment_menu.py
elif python -c "import numpy" 2>/dev/null; then
    echo "使用 python 執行..."
    python test/experiment_menu.py
else
    echo "錯誤：無法找到可用的 Python 環境"
    exit 1
fi
EOF

chmod +x run_experiment_safe.sh

echo ""
echo "已創建 run_experiment_safe.sh 腳本"
echo "使用方法: ./run_experiment_safe.sh"