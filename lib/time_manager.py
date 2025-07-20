"""
統一時間管理系統
==============

解決RMFS系統中多種時間單位混用的問題
"""

class TimeManager:
    """統一時間管理類"""
    
    TICK_TO_SECOND = 0.15
    
    @classmethod
    def warehouse_to_real(cls, tick: float) -> float:
        """倉庫時間轉換為現實時間（秒）"""
        return tick * cls.TICK_TO_SECOND
    
    @classmethod
    def real_to_warehouse(cls, seconds: float) -> float:
        """現實時間（秒）轉換為倉庫時間"""
        return seconds / cls.TICK_TO_SECOND
    
    @classmethod
    def format_time(cls, warehouse_tick: float, show_real: bool = True) -> str:
        """格式化時間顯示"""
        if show_real:
            real_time = cls.warehouse_to_real(warehouse_tick)
            return f"[倉庫Tick {warehouse_tick:.1f} | {real_time:.1f}秒]"
        return f"[倉庫Tick {warehouse_tick:.1f}]"
    
    @classmethod
    def format_training_progress(cls, python_tick: int, total_ticks: int, warehouse_tick: float = None) -> str:
        """格式化訓練進度"""
        progress = f"[訓練進度 {python_tick}/{total_ticks}]"
        if warehouse_tick is not None:
            real_time = cls.warehouse_to_real(warehouse_tick)
            progress += f" [模擬時間 {warehouse_tick:.1f}t/{real_time:.1f}s]"
        return progress
    
    @classmethod
    def estimate_real_duration(cls, ticks: int) -> str:
        """預估實際運行時間"""
        total_seconds = cls.warehouse_to_real(ticks)
        if total_seconds < 60:
            return f"{total_seconds:.1f}秒"
        elif total_seconds < 3600:
            minutes = total_seconds / 60
            return f"{minutes:.1f}分鐘"
        else:
            hours = total_seconds / 3600
            return f"{hours:.1f}小時"

# 便捷函數
def format_time(warehouse_tick: float, show_real: bool = True) -> str:
    """便捷的時間格式化函數"""
    return TimeManager.format_time(warehouse_tick, show_real)

def warehouse_to_real(tick: float) -> float:
    """便捷的時間轉換函數"""
    return TimeManager.warehouse_to_real(tick)

# 倉庫內重要時間設定的含義
WAREHOUSE_TIME_MEANINGS = {
    "紅綠燈週期": {
        "horizontal_green_time": 70,  # 倉庫 ticks = 10.5 現實秒
        "vertical_green_time": 30,    # 倉庫 ticks = 4.5 現實秒  
        "total_cycle": 100,           # 倉庫 ticks = 15 現實秒
        "meaning": "機器人看到的紅綠燈每15秒循環一次"
    },
    "訂單時間": {
        "order_cycle_time": 100,      # 每小時100個訂單
        "order_period_time": 5,       # 總共5小時
        "meaning": "模擬5小時的訂單，每小時100個"
    },
    "機器人物理": {
        "max_velocity": 1.5,          # 單位/tick = 10 單位/現實秒
        "acceleration": 1.0,          # 單位/tick² = 44.4 單位/現實秒²
        "meaning": "機器人最高速度約每秒10個倉庫格，加速度很高"
    },
    "等待閾值": {
        "max_wait_threshold": 50,     # 倉庫 ticks = 7.5 現實秒
        "meaning": "機器人等待超過7.5秒就會觸發緊急模式"
    }
}