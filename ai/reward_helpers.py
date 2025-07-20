# ai/reward_helpers.py
"""
獎勵系統輔助函數
提供里程碑檢查和路徑分析功能，避免污染核心業務邏輯
"""

from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def is_last_milestone(robot, warehouse) -> bool:
    """
    動態檢查機器人是否剛剛通過了通往目的地的最後一個受控路口
    
    Args:
        robot: 機器人對象
        warehouse: 倉庫對象
        
    Returns:
        bool: 是否通過了最後一個受控路口
    """
    if robot.current_state != 'delivering_pod':
        return False
    
    # 檢查剩餘路徑點是否還有路口
    if not hasattr(robot, 'route_stop_points') or not robot.route_stop_points:
        return False
        
    # 獲取所有路口位置
    intersections = warehouse.intersection_manager.intersections
    intersection_coords = set()
    for intersection in intersections:
        intersection_coords.add((intersection.pos_x, intersection.pos_y))
    
    # 檢查剩餘路徑中是否還有路口
    for point in robot.route_stop_points:
        if hasattr(point, 'x') and hasattr(point, 'y'):
            if (point.x, point.y) in intersection_coords:
                return False  # 還有路口要經過
        elif hasattr(point, 'pos_x') and hasattr(point, 'pos_y'):
            if (point.pos_x, point.pos_y) in intersection_coords:
                return False  # 還有路口要經過
    
    return True  # 路徑上已無路口，剛剛通過的是最後一個

def is_first_return_intersection(robot, warehouse) -> bool:
    """
    檢查機器人是否剛剛通過了離開揀貨區後的第一個受控路口
    
    Args:
        robot: 機器人對象
        warehouse: 倉庫對象
        
    Returns:
        bool: 是否通過了第一個返回路口
    """
    if robot.current_state != 'returning_pod':
        return False
    
    # 檢查是否有標記的第一個返回路口
    if hasattr(robot, 'first_return_intersection'):
        current_intersection = get_current_intersection(robot, warehouse)
        if current_intersection and id(current_intersection) == robot.first_return_intersection:
            return True
    
    return False

def get_current_intersection(robot, warehouse):
    """
    獲取機器人當前所在的路口
    
    Args:
        robot: 機器人對象
        warehouse: 倉庫對象
        
    Returns:
        Intersection: 當前路口對象，如果不在路口則返回None
    """
    robot_pos = getattr(robot, 'coordinate', None)
    if not robot_pos:
        return None
    
    # 檢查所有路口
    for intersection in warehouse.intersection_manager.intersections:
        # 使用一定的容差範圍判斷是否在路口
        if (abs(intersection.pos_x - robot_pos.x) < 0.5 and 
            abs(intersection.pos_y - robot_pos.y) < 0.5):
            return intersection
    
    return None

def get_intersections_from_path(route_stop_points, warehouse) -> List[Tuple[int, int]]:
    """
    從路徑點中提取所有路口坐標
    
    Args:
        route_stop_points: 路徑點列表
        warehouse: 倉庫對象
        
    Returns:
        List[Tuple[int, int]]: 路口坐標列表
    """
    if not route_stop_points or not warehouse:
        return []
    
    intersections = warehouse.intersection_manager.intersections
    intersection_coords = set()
    for intersection in intersections:
        intersection_coords.add((intersection.pos_x, intersection.pos_y))
    
    path_intersections = []
    for point in route_stop_points:
        if hasattr(point, 'x') and hasattr(point, 'y'):
            if (point.x, point.y) in intersection_coords:
                path_intersections.append((point.x, point.y))
        elif hasattr(point, 'pos_x') and hasattr(point, 'pos_y'):
            if (point.pos_x, point.pos_y) in intersection_coords:
                path_intersections.append((point.pos_x, point.pos_y))
    
    return path_intersections

def check_and_log_milestones(robot, warehouse, reward_system):
    """
    統一的里程碑檢查函數，在機器人離開路口時調用
    
    Args:
        robot: 機器人對象
        warehouse: 倉庫對象
        reward_system: 獎勵系統對象
    """
    try:
        # 1. 檢查「護送至揀貨區」里程碑
        if is_last_milestone(robot, warehouse):
            reward_system._log_milestone_event(reward_system.weights['milestone_delivery'])
            logger.debug(f"機器人 {robot.robotName()} 達成護送至揀貨區里程碑")
        
        # 2. 檢查「釋放揀貨區」里程碑
        if is_first_return_intersection(robot, warehouse):
            reward_system._log_milestone_event(reward_system.weights['milestone_return'])
            logger.debug(f"機器人 {robot.robotName()} 達成釋放揀貨區里程碑")
            # 防止重複獎勵
            if hasattr(robot, 'first_return_intersection'):
                delattr(robot, 'first_return_intersection')
    
    except Exception as e:
        logger.error(f"里程碑檢查發生錯誤: {e}")

def setup_first_return_intersection(robot, warehouse):
    """
    當機器人狀態變為 returning_pod 時，設置第一個返回路口標記
    
    Args:
        robot: 機器人對象
        warehouse: 倉庫對象
    """
    try:
        if robot.current_state == 'returning_pod' and hasattr(robot, 'route_stop_points'):
            path_intersections = get_intersections_from_path(robot.route_stop_points, warehouse)
            if path_intersections:
                # 找到對應的路口對象並記錄其ID
                for intersection in warehouse.intersection_manager.intersections:
                    if (intersection.pos_x, intersection.pos_y) == path_intersections[0]:
                        robot.first_return_intersection = id(intersection)
                        logger.debug(f"設置機器人 {robot.robotName()} 第一個返回路口: {path_intersections[0]}")
                        break
    except Exception as e:
        logger.error(f"設置第一個返回路口時發生錯誤: {e}")

def get_robot_task_priority(robot) -> str:
    """
    根據機器人狀態返回任務優先級
    
    Args:
        robot: 機器人對象
        
    Returns:
        str: 優先級 ('high', 'medium', 'low')
    """
    state = getattr(robot, 'current_state', 'idle')
    
    if state == 'delivering_pod':
        return 'high'
    elif state == 'returning_pod':
        return 'medium'
    elif state == 'taking_pod':
        return 'low'
    else:
        return 'low'  # idle 或其他狀態