#!/bin/bash

# RunPod 中文環境設置腳本
# 用於解決 Python 程式中文顯示亂碼問題

echo "========================================="
echo "開始設置 RunPod 中文環境..."
echo "========================================="

# 檢查是否為 root 用戶
if [ "$EUID" -ne 0 ]; then 
    echo "注意：非 root 用戶，嘗試不使用 sudo 執行..."
fi

# 更新套件列表
echo "1. 更新套件列表..."
apt update

# 安裝中文語言包
echo "2. 安裝中文語言包..."
apt install -y language-pack-zh-hant language-pack-zh-hans || apt install -y locales

# 安裝中文字體
echo "3. 安裝中文字體..."
apt install -y fonts-noto-cjk fonts-wqy-microhei fonts-wqy-zenhei

# 安裝 screen（如果尚未安裝）
echo "4. 安裝 screen..."
apt install -y screen

# 生成中文 locale
echo "5. 生成中文 locale..."
locale-gen zh_TW.UTF-8
locale-gen zh_CN.UTF-8
locale-gen en_US.UTF-8

# 更新 locale
echo "6. 更新 locale 設定..."
update-locale LANG=zh_TW.UTF-8

# 設置環境變數
echo "7. 設置環境變數..."
if ! grep -q "export LANG=zh_TW.UTF-8" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# 中文環境設置
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8
export PYTHONIOENCODING=utf-8
EOF
fi

# 設置 screen 支援中文
echo "8. 配置 screen 支援中文..."
if [ ! -f ~/.screenrc ]; then
    touch ~/.screenrc
fi

if ! grep -q "defutf8 on" ~/.screenrc; then
    cat >> ~/.screenrc << 'EOF'
# UTF-8 支援
defutf8 on
encoding UTF-8 UTF-8
EOF
fi

# 立即應用設置
echo "9. 立即應用環境設置..."
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8
export PYTHONIOENCODING=utf-8

# 測試中文顯示
echo "========================================="
echo "10. 測試中文顯示..."
echo "測試中文：你好，世界！"
python3 -c "print('Python 測試中文：你好，世界！')" 2>/dev/null || python -c "print('Python 測試中文：你好，世界！')"

echo "========================================="
echo "中文環境設置完成！"
echo ""
echo "使用說明："
echo "1. 執行 'source ~/.bashrc' 以載入新的環境變數"
echo "2. 或重新開啟終端"
echo ""
echo "使用 screen 的方法："
echo "- 創建會話：screen -U -S experiment"
echo "- 脫離會話：按 Ctrl+A 然後按 D"
echo "- 重新連接：screen -r experiment"
echo "========================================="