"""
V7.0: 速度限制管理器
管理整條路的限速，不只是單個路口
"""
from typing import Dict, List, Tuple, Optional
from world.entities.robot import Robot
from world.entities.intersection import Intersection

class SpeedLimitManager:
    """管理倉庫中的速度限制區域"""
    
    def __init__(self, warehouse):
        self.warehouse = warehouse
        # 限速區域：(x1, y1, x2, y2) -> speed_factor
        self.speed_zones: Dict[Tuple[int, int, int, int], float] = {}
        
    def set_corridor_speed_limit(self, intersection_id: int, speed_factor: float, corridor_type: str = "both"):
        """
        設定通過特定路口的整條走廊的限速
        
        Args:
            intersection_id: 路口ID
            speed_factor: 速度係數 (0.3-1.0)
            corridor_type: "horizontal", "vertical", 或 "both"
        """
        # 獲取路口
        intersection = self.warehouse.intersection_manager.intersection_id_to_intersection.get(intersection_id)
        if not intersection:
            return
            
        x, y = intersection.pos_x, intersection.pos_y
        
        # 設定水平走廊（整條橫向道路）
        if corridor_type in ["horizontal", "both"]:
            # 假設倉庫寬度為60
            self.speed_zones[(0, y, 60, y)] = speed_factor
            
        # 設定垂直走廊（整條縱向道路）
        if corridor_type in ["vertical", "both"]:
            # 假設倉庫高度為60
            self.speed_zones[(x, 0, x, 60)] = speed_factor
            
        # 應用限速到所有在該區域的機器人
        self._apply_speed_limits()
    
    def remove_corridor_speed_limit(self, intersection_id: int, corridor_type: str = "both"):
        """移除特定走廊的限速"""
        intersection = self.warehouse.intersection_manager.intersection_id_to_intersection.get(intersection_id)
        if not intersection:
            return
            
        x, y = intersection.pos_x, intersection.pos_y
        
        # 移除對應的限速區域
        zones_to_remove = []
        for zone in self.speed_zones:
            x1, y1, x2, y2 = zone
            if corridor_type in ["horizontal", "both"] and y1 == y == y2:
                zones_to_remove.append(zone)
            if corridor_type in ["vertical", "both"] and x1 == x == x2:
                zones_to_remove.append(zone)
                
        for zone in zones_to_remove:
            del self.speed_zones[zone]
            
        # 重新應用限速（可能需要恢復某些機器人的速度）
        self._apply_speed_limits()
    
    def _apply_speed_limits(self):
        """應用限速到所有機器人"""
        for robot in self.warehouse.robot_manager.robots:
            # 檢查機器人是否在任何限速區域內
            robot_x, robot_y = round(robot.pos_x), round(robot.pos_y)
            
            # 找出最嚴格的限速
            min_speed_factor = 1.0
            in_speed_zone = False
            
            for (x1, y1, x2, y2), speed_factor in self.speed_zones.items():
                if (min(x1, x2) <= robot_x <= max(x1, x2) and 
                    min(y1, y2) <= robot_y <= max(y1, y2)):
                    in_speed_zone = True
                    min_speed_factor = min(min_speed_factor, speed_factor)
            
            # 應用或移除限速
            if in_speed_zone:
                robot.apply_speed_limit(min_speed_factor)
            else:
                robot.remove_speed_limit()
    
    def get_active_speed_zones(self) -> List[Dict]:
        """獲取所有活躍的限速區域信息"""
        zones = []
        for (x1, y1, x2, y2), speed_factor in self.speed_zones.items():
            zones.append({
                'zone': (x1, y1, x2, y2),
                'speed_factor': speed_factor,
                'speed_percentage': f"{speed_factor * 100:.0f}%"
            })
        return zones
    
    def update(self, tick):
        """每個tick更新，確保新進入限速區的機器人被正確限速"""
        if tick % 10 == 0:  # 每10個tick檢查一次
            self._apply_speed_limits()