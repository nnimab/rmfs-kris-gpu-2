@echo off
REM RMFS 容量測試啟動腳本
REM 確保使用正確的 venv 環境

cd /d "%~dp0\.."

echo ===================================
echo RMFS 容量測試系統
echo ===================================
echo.

REM 檢查 venv 是否存在
if not exist ".venv\Scripts\activate.bat" (
    echo 錯誤：找不到虛擬環境 .venv
    echo 請先建立虛擬環境：python -m venv .venv
    pause
    exit /b 1
)

REM 啟動虛擬環境
echo 正在啟動虛擬環境...
call .venv\Scripts\activate.bat

echo.
echo 當前 Python 資訊：
python --version
where python

echo.
echo 檢查必要套件...
python -c "import torch; print(f'PyTorch {torch.__version__} 已安裝')" 2>nul || (
    echo.
    echo 缺少必要套件，正在安裝...
    pip install -r requirements.txt
)

echo.
echo 啟動容量測試選單...
echo.

REM 使用明確的 python 路徑執行
python test\experiment_menu.py

pause