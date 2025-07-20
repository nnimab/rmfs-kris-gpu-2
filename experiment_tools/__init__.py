"""
RMFS 實驗自動化工具包
====================

簡潔的實驗管理系統，專注於核心功能：
- 🤖 AI模型訓練
- 📊 效能驗證  
- 📈 數據分析與圖表
- 🚀 完整實驗流程
- ⚙️ 自定義參數設置

作者: Claude AI Assistant
版本: 1.0
日期: 2025-07-09
"""

__version__ = "1.0.0"
__author__ = "Claude AI Assistant"
__description__ = "RMFS 實驗自動化管理系統"

from .presets import EXPERIMENT_PRESETS
from .config_manager import ConfigManager
from .workflow_runner import WorkflowRunner

__all__ = [
    'EXPERIMENT_PRESETS',
    'ConfigManager', 
    'WorkflowRunner'
]