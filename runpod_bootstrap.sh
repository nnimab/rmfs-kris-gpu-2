#!/usr/bin/env bash

set -euo pipefail

log() { echo -e "\n========================================="; echo "[RunPod Bootstrap] $*"; };

# Options
START_EXPERIMENT=${START_EXPERIMENT:-1}
SESSION_NAME=${SESSION_NAME:-experiment}
PY_BIN=""

detect_python() {
  if command -v python3 >/dev/null 2>&1; then PY_BIN=python3; elif command -v python >/dev/null 2>&1; then PY_BIN=python; else echo "Python not found" >&2; exit 1; fi
}

install_apt_packages() {
  if command -v apt >/dev/null 2>&1; then
    log "更新套件列表 (apt)"
    sudo apt update || apt update || true
    log "安裝中文語言包/字體與 screen"
    sudo apt install -y locales language-pack-zh-hant language-pack-zh-hans || sudo apt install -y locales || true
    sudo apt install -y fonts-noto-cjk fonts-wqy-microhei fonts-wqy-zenhei || true
    sudo apt install -y screen || true
  fi
}

configure_locale() {
  log "配置中文 locale 與環境變數"
  if command -v locale-gen >/dev/null 2>&1; then
    sudo locale-gen zh_TW.UTF-8 || true
    sudo locale-gen zh_CN.UTF-8 || true
    sudo locale-gen en_US.UTF-8 || true
  fi
  if command -v update-locale >/dev/null 2>&1; then
    sudo update-locale LANG=zh_TW.UTF-8 || true
  fi

  # 永久環境變數
  if ! grep -q "export LANG=zh_TW.UTF-8" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" << 'EOF'

# 中文環境設置（RunPod Bootstrap）
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8
export PYTHONIOENCODING=utf-8
EOF
  fi

  export LANG=zh_TW.UTF-8
  export LC_ALL=zh_TW.UTF-8
  export PYTHONIOENCODING=utf-8

  # screen UTF-8
  if [ ! -f "$HOME/.screenrc" ] || ! grep -q "defutf8 on" "$HOME/.screenrc"; then
    cat >> "$HOME/.screenrc" << 'EOF'
# UTF-8 支援（RunPod Bootstrap）
defutf8 on
encoding UTF-8 UTF-8
EOF
  fi
}

pip_install_requirements() {
  log "升級 pip"
  "$PY_BIN" -m pip install --upgrade pip

  if [ -f requirements.txt ]; then
    log "安裝 requirements.txt"
    "$PY_BIN" -m pip install -r requirements.txt --upgrade-strategy only-if-needed || true

    # 測試 NumPy；若失敗走修復路徑
    if ! "$PY_BIN" - <<'PY'
import sys
try:
    import numpy as np
    print('NumPy OK:', np.__version__)
    sys.exit(0)
except Exception as e:
    print('NumPy import failed:', e)
    sys.exit(1)
PY
    then
      log "修復 NumPy 相容性（安裝 numpy==1.23.5 並重試 requirements）"
      "$PY_BIN" -m pip uninstall -y numpy || true
      "$PY_BIN" -m pip install --no-cache-dir numpy==1.23.5
      "$PY_BIN" -m pip install -r requirements.txt --upgrade-strategy only-if-needed || true
      "$PY_BIN" - <<'PY'
import sys
import numpy as np
print('NumPy after fix:', np.__version__)
PY
    fi
  else
    log "未找到 requirements.txt，略過套件安裝"
  fi
}

start_screen_experiment() {
  if [ "${START_EXPERIMENT}" != "1" ]; then
    log "跳過自動啟動實驗（START_EXPERIMENT!=1）"
    return 0
  fi

  if ! command -v screen >/dev/null 2>&1; then
    log "screen 未安裝，略過背景啟動；直接前台執行"
    exec "$PY_BIN" test/experiment_menu.py
  fi

  # 如果同名會話存在，先關閉
  if screen -list | grep -q "\.${SESSION_NAME}\b"; then
    log "存在舊的 screen 會話，嘗試結束: ${SESSION_NAME}"
    screen -S "${SESSION_NAME}" -X quit || true
    sleep 1
  fi

  log "啟動 screen 會話: ${SESSION_NAME}"
  screen -U -S "${SESSION_NAME}" -dm bash -lc "${PY_BIN} test/experiment_menu.py"
  echo "已在背景啟動。附加會話: screen -r ${SESSION_NAME}"
}

# Main
log "RunPod Bootstrap 開始"
detect_python
install_apt_packages
configure_locale
pip_install_requirements
start_screen_experiment
log "完成"

cat << 'USAGE'

使用說明:
  bash runpod_bootstrap.sh            # 一鍵設置 + 背景啟動選單 (screen 會話名: experiment)

環境變數:
  START_EXPERIMENT=0                 # 不自動啟動實驗
  SESSION_NAME=experiment            # 指定 screen 會話名稱

附加/管理畫面:
  screen -r experiment               # 附加到會話
  Ctrl+A 然後 D                      # 脫離會話
  screen -ls                          # 列出會話
  screen -S experiment -X quit       # 結束會話
USAGE


