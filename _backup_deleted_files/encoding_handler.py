#!/usr/bin/env python3
"""
Windows編碼處理器 - 解決Unicode表情符號在Windows cp950環境下的顯示問題
"""

import sys
import locale
import os
from typing import Dict, Optional

class EncodingHandler:
    """處理不同編碼環境下的安全輸出"""
    
    def __init__(self):
        self.system_encoding = self.detect_system_encoding()
        self.safe_mode = self.system_encoding in ['cp950', 'gbk', 'ascii']
        
        # Unicode表情符號到ASCII的映射
        self.emoji_map = {
            '🔍': '[SCAN]',
            '📁': '[DIR]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '🧪': '[TEST]',
            '📊': '[CHART]',
            '🎯': '[TARGET]',
            '⚠️': '[WARN]',
            '💡': '[TIP]',
            '📈': '[GRAPH]',
            '📝': '[REPORT]',
            '🖥️': '[PC]',
            '🚀': '[LAUNCH]',
            '🔧': '[TOOL]',
            '📄': '[FILE]',
            '👋': '[BYE]',
            '🌟': '[STAR]',
            '⭐': '[STAR]',
            '🎉': '[PARTY]',
            '💻': '[COMPUTER]',
            '📋': '[CLIPBOARD]',
            '🔄': '[REFRESH]',
            '⏰': '[TIME]',
            '📦': '[PACKAGE]',
            '🛠️': '[TOOLS]',
            '🎨': '[ART]',
            '📱': '[PHONE]',
            '🌐': '[WEB]',
            '🔒': '[LOCK]',
            '🔓': '[UNLOCK]',
            '🎪': '[CIRCUS]',
            '🎭': '[MASK]',
            '🎬': '[MOVIE]',
            '🎮': '[GAME]',
            '🎲': '[DICE]',
            '🎯': '[DART]',
            '🎸': '[GUITAR]',
            '🎹': '[PIANO]',
            '🎺': '[TRUMPET]',
            '🎻': '[VIOLIN]',
            '🥁': '[DRUM]',
            '🎤': '[MIC]',
            '🎧': '[HEADPHONE]',
            '📻': '[RADIO]',
            '📺': '[TV]',
            '📷': '[CAMERA]',
            '📹': '[VIDEO]',
            '💾': '[DISK]',
            '💿': '[CD]',
            '📀': '[DVD]',
            '🖨️': '[PRINTER]',
            '⌨️': '[KEYBOARD]',
            '🖱️': '[MOUSE]',
            '🖥️': '[MONITOR]',
            '💻': '[LAPTOP]',
            '📱': '[MOBILE]',
            '☎️': '[PHONE]',
            '📞': '[CALL]',
            '📟': '[PAGER]',
            '📠': '[FAX]',
            '📡': '[SATELLITE]',
            '🔋': '[BATTERY]',
            '🔌': '[PLUG]',
            '💡': '[BULB]',
            '🔦': '[FLASHLIGHT]',
            '🕯️': '[CANDLE]',
            '🪔': '[LAMP]',
            '🔥': '[FIRE]',
            '💧': '[WATER]',
            '🌊': '[WAVE]',
            '❄️': '[SNOW]',
            '⛄': '[SNOWMAN]',
            '☀️': '[SUN]',
            '🌙': '[MOON]',
            '⭐': '[STAR]',
            '🌟': '[SPARKLE]',
            '⚡': '[LIGHTNING]',
            '🌈': '[RAINBOW]',
            '☁️': '[CLOUD]',
            '⛅': '[PARTLY_CLOUDY]',
            '🌤️': '[SUN_CLOUD]',
            '🌦️': '[RAIN_SUN]',
            '🌧️': '[RAIN]',
            '⛈️': '[STORM]',
            '🌩️': '[LIGHTNING_CLOUD]',
            '❄️': '[SNOW]',
            '☃️': '[SNOWMAN]',
            '⛄': '[SNOWMAN2]',
            '🌨️': '[SNOW_CLOUD]',
            '💨': '[WIND]',
            '🌪️': '[TORNADO]',
            '🌫️': '[FOG]',
            '🌊': '[OCEAN]',
            '💧': '[DROPLET]',
            '💦': '[SWEAT]',
            '☔': '[UMBRELLA_RAIN]',
            '☂️': '[UMBRELLA]',
            '🌂': '[UMBRELLA2]',
            '⛱️': '[BEACH_UMBRELLA]'
        }
        
        # 狀態前綴映射
        self.status_prefixes = {
            'success': '[OK]' if self.safe_mode else '✅',
            'error': '[ERROR]' if self.safe_mode else '❌',
            'warning': '[WARN]' if self.safe_mode else '⚠️',
            'info': '[INFO]' if self.safe_mode else 'ℹ️',
            'scan': '[SCAN]' if self.safe_mode else '🔍',
            'chart': '[CHART]' if self.safe_mode else '📊',
            'file': '[FILE]' if self.safe_mode else '📄',
            'dir': '[DIR]' if self.safe_mode else '📁',
            'tip': '[TIP]' if self.safe_mode else '💡',
            'test': '[TEST]' if self.safe_mode else '🧪',
            'target': '[TARGET]' if self.safe_mode else '🎯',
            'report': '[REPORT]' if self.safe_mode else '📝',
            'graph': '[GRAPH]' if self.safe_mode else '📈',
            'pc': '[PC]' if self.safe_mode else '🖥️'
        }
    
    def detect_system_encoding(self) -> str:
        """檢測系統編碼"""
        try:
            # 檢查標準輸出編碼
            if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
                encoding = sys.stdout.encoding.lower()
                if 'cp950' in encoding or 'big5' in encoding:
                    return 'cp950'
                elif 'gbk' in encoding or 'gb2312' in encoding:
                    return 'gbk'
                elif 'utf-8' in encoding or 'utf8' in encoding:
                    return 'utf-8'
            
            # 檢查系統locale
            try:
                system_encoding = locale.getpreferredencoding().lower()
                if 'cp950' in system_encoding or 'big5' in system_encoding:
                    return 'cp950'
                elif 'gbk' in system_encoding:
                    return 'gbk'
                elif 'utf-8' in system_encoding or 'utf8' in system_encoding:
                    return 'utf-8'
            except:
                pass
            
            # Windows特殊檢查
            if os.name == 'nt':
                return 'cp950'  # Windows中文環境預設
            
            return 'utf-8'  # 預設為UTF-8
            
        except Exception:
            return 'ascii'  # 最安全的選擇
    
    def safe_print(self, message: str, end: str = '\n', flush: bool = False) -> None:
        """安全的print函數，自動處理編碼問題"""
        try:
            if self.safe_mode:
                # 替換所有Unicode表情符號
                safe_message = self.unicode_to_ascii(message)
                print(safe_message, end=end, flush=flush)
            else:
                print(message, end=end, flush=flush)
        except UnicodeEncodeError:
            # 如果仍然失敗，強制使用ASCII版本
            safe_message = self.unicode_to_ascii(message)
            try:
                print(safe_message, end=end, flush=flush)
            except:
                # 最後手段：移除所有非ASCII字符
                ascii_only = ''.join(char for char in safe_message if ord(char) < 128)
                print(ascii_only, end=end, flush=flush)
    
    def unicode_to_ascii(self, text: str) -> str:
        """將Unicode表情符號轉換為ASCII替代"""
        result = text
        for emoji, replacement in self.emoji_map.items():
            result = result.replace(emoji, replacement)
        return result
    
    def format_status(self, status: str, message: str) -> str:
        """格式化狀態訊息"""
        prefix = self.status_prefixes.get(status.lower(), f'[{status.upper()}]')
        return f"{prefix} {message}"
    
    def print_status(self, status: str, message: str, **kwargs) -> None:
        """打印狀態訊息"""
        formatted_message = self.format_status(status, message)
        self.safe_print(formatted_message, **kwargs)
    
    def print_success(self, message: str, **kwargs) -> None:
        """打印成功訊息"""
        self.print_status('success', message, **kwargs)
    
    def print_error(self, message: str, **kwargs) -> None:
        """打印錯誤訊息"""
        self.print_status('error', message, **kwargs)
    
    def print_warning(self, message: str, **kwargs) -> None:
        """打印警告訊息"""
        self.print_status('warning', message, **kwargs)
    
    def print_info(self, message: str, **kwargs) -> None:
        """打印資訊訊息"""
        self.print_status('info', message, **kwargs)
    
    def print_scan(self, message: str, **kwargs) -> None:
        """打印掃描訊息"""
        self.print_status('scan', message, **kwargs)
    
    def print_chart(self, message: str, **kwargs) -> None:
        """打印圖表訊息"""
        self.print_status('chart', message, **kwargs)

# 創建全局實例
encoder = EncodingHandler()

# 提供便捷函數
def safe_print(message: str, **kwargs) -> None:
    """全局安全print函數"""
    encoder.safe_print(message, **kwargs)

def print_success(message: str, **kwargs) -> None:
    """全局成功訊息函數"""
    encoder.print_success(message, **kwargs)

def print_error(message: str, **kwargs) -> None:
    """全局錯誤訊息函數"""
    encoder.print_error(message, **kwargs)

def print_warning(message: str, **kwargs) -> None:
    """全局警告訊息函數"""
    encoder.print_warning(message, **kwargs)

def print_info(message: str, **kwargs) -> None:
    """全局資訊訊息函數"""
    encoder.print_info(message, **kwargs)

def print_scan(message: str, **kwargs) -> None:
    """全局掃描訊息函數"""
    encoder.print_scan(message, **kwargs)

def print_chart(message: str, **kwargs) -> None:
    """全局圖表訊息函數"""
    encoder.print_chart(message, **kwargs)

if __name__ == "__main__":
    # 測試編碼處理器
    print("Testing EncodingHandler...")
    print(f"System encoding: {encoder.system_encoding}")
    print(f"Safe mode: {encoder.safe_mode}")
    print()
    
    # 測試各種狀態訊息
    encoder.print_success("測試成功訊息")
    encoder.print_error("測試錯誤訊息")
    encoder.print_warning("測試警告訊息")
    encoder.print_info("測試資訊訊息")
    encoder.print_scan("測試掃描訊息")
    encoder.print_chart("測試圖表訊息")
    
    # 測試Unicode轉換
    test_message = "🔍 開始分析... ✅ 成功載入 📊 生成圖表"
    print(f"\nOriginal: {test_message}")
    print(f"Converted: {encoder.unicode_to_ascii(test_message)}")