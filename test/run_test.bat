@echo off
REM 確保使用 venv 環境執行測試

cd /d "%~dp0\.."

echo 啟動虛擬環境...
call .venv\Scripts\activate.bat

echo.
echo 當前 Python 路徑:
where python

echo.
echo 當前 pip 路徑:
where pip

echo.
echo 檢查已安裝套件...
python -m pip list | findstr torch

echo.
echo 開始執行測試...
python test\experiment_menu.py

pause