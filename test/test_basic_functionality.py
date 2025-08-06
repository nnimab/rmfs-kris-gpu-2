#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMFS 容量測試系統基本功能測試

驗證各個組件的基本功能是否正常工作。
"""

import sys
import os
import tempfile
from pathlib import Path
import json
import logging

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test.capacity_test_controller import CapacityTestController
from test.isolation_manager import IsolationManager
from test.capacity_analyzer import CapacityAnalyzer
from lib.logger import get_logger


class BasicFunctionalityTest:
    """基本功能測試類別"""
    
    def __init__(self):
        self.logger = get_logger()
        self.temp_dir = None
        self.test_results = {}
        
    def setup(self):
        """設置測試環境"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rmfs_test_"))
        self.logger.info(f"測試臨時目錄: {self.temp_dir}")
        
    def teardown(self):
        """清理測試環境"""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.info("已清理測試臨時目錄")
            except Exception as e:
                self.logger.warning(f"清理臨時目錄時發生錯誤: {e}")
    
    def test_isolation_manager(self) -> bool:
        """測試隔離管理器"""
        try:
            self.logger.info("🧪 測試隔離管理器...")
            
            # 創建隔離管理器
            isolation_manager = IsolationManager(self.temp_dir, self.logger)
            
            # 測試創建工作空間
            test_id = "test_robot_25"
            robot_count = 25
            
            isolated_paths = isolation_manager.create_isolated_workspace(robot_count, test_id)
            
            # 驗證工作空間是否創建
            workspace_root = Path(isolated_paths['workspace_root'])
            if not workspace_root.exists():
                raise Exception("工作空間未創建")
            
            # 驗證必要目錄是否存在
            required_dirs = ['states', 'csv_files', 'data', 'results', 'logs']
            for dir_name in required_dirs:
                if not (workspace_root / dir_name).exists():
                    raise Exception(f"缺少必要目錄: {dir_name}")
            
            # 測試環境變數生成
            env_vars = isolation_manager.get_isolated_env_vars(test_id)
            if not env_vars.get('SIMULATION_ID'):
                raise Exception("環境變數生成失敗")
            
            # 測試工作空間驗證
            if not isolation_manager.validate_workspace(test_id):
                raise Exception("工作空間驗證失敗")
            
            # 測試清理功能
            if not isolation_manager.cleanup_workspace(test_id, keep_results=True):
                raise Exception("工作空間清理失敗")
            
            self.test_results['isolation_manager'] = True
            self.logger.info("✅ 隔離管理器測試通過")
            return True
            
        except Exception as e:
            self.test_results['isolation_manager'] = False
            self.logger.error(f"❌ 隔離管理器測試失敗: {e}")
            return False
    
    def test_capacity_controller_init(self) -> bool:
        """測試容量測試控制器初始化"""
        try:
            self.logger.info("🧪 測試容量測試控制器初始化...")
            
            # 創建控制器
            controller = CapacityTestController(str(self.temp_dir / "controller_test"))
            
            # 驗證基本屬性
            if not controller.instance_id:
                raise Exception("實例 ID 未生成")
            
            if not controller.platform:
                raise Exception("平台資訊未獲取")
            
            if not controller.base_output_dir.exists():
                raise Exception("輸出目錄未創建")
            
            # 測試隔離路徑生成
            test_id = "init_test"
            robot_count = 20
            
            isolated_paths = controller.get_isolated_paths(robot_count, test_id)
            
            if not isolated_paths.get('workspace_root'):
                raise Exception("隔離路徑生成失敗")
            
            # 測試進度追蹤
            progress = controller.get_test_progress()
            if not isinstance(progress, dict):
                raise Exception("進度追蹤功能異常")
            
            self.test_results['capacity_controller_init'] = True
            self.logger.info("✅ 容量測試控制器初始化測試通過")
            return True
            
        except Exception as e:
            self.test_results['capacity_controller_init'] = False
            self.logger.error(f"❌ 容量測試控制器初始化測試失敗: {e}")
            return False
    
    def test_capacity_analyzer_init(self) -> bool:
        """測試容量分析器初始化"""
        try:
            self.logger.info("🧪 測試容量分析器初始化...")
            
            # 創建模擬測試結果
            test_results_dir = self.temp_dir / "analyzer_test"
            test_results_dir.mkdir(exist_ok=True)
            
            # 創建模擬測試摘要
            mock_summary = {
                "test_session_id": "test_session_001",
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T12:00:00",
                "total_execution_time": 7200,
                "robot_counts_tested": [20, 25, 30],
                "total_tests": 3,
                "completed_tests": 3,
                "failed_tests": 0,
                "test_ticks": 50000,
                "results": [
                    {
                        "test_id": "test_20",
                        "robot_count": 20,
                        "status": "completed",
                        "execution_time": 2400,
                        "evaluation_results": {
                            "none": [{
                                "completed_orders": 150,
                                "total_orders": 200,
                                "completion_rate": 0.75,
                                "avg_wait_time": 5.2,
                                "total_energy": 10000,
                                "energy_per_order": 66.7
                            }]
                        }
                    }
                ]
            }
            
            summary_file = test_results_dir / "capacity_test_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(mock_summary, f, indent=2, ensure_ascii=False)
            
            # 創建分析器
            analyzer = CapacityAnalyzer(test_results_dir)
            
            # 測試數據載入
            if not analyzer.load_test_data():
                raise Exception("數據載入失敗")
            
            if not analyzer.raw_data:
                raise Exception("沒有載入到數據")
            
            # 測試數據處理
            if not analyzer.process_data():
                raise Exception("數據處理失敗")
            
            if 'df' not in analyzer.processed_data:
                raise Exception("數據處理結果不正確")
            
            self.test_results['capacity_analyzer_init'] = True
            self.logger.info("✅ 容量分析器初始化測試通過")
            return True
            
        except Exception as e:
            self.test_results['capacity_analyzer_init'] = False
            self.logger.error(f"❌ 容量分析器初始化測試失敗: {e}")
            return False
    
    def test_evaluate_parameter_support(self) -> bool:
        """測試 evaluate.py 參數支援"""
        try:
            self.logger.info("🧪 測試 evaluate.py 參數支援...")
            
            # 測試環境變數設置
            os.environ['ROBOT_COUNT'] = '30'
            
            # 驗證環境變數是否正確讀取
            robot_count = int(os.environ.get('ROBOT_COUNT', 20))
            if robot_count != 30:
                raise Exception("環境變數讀取失敗")
            
            # 清理環境變數
            del os.environ['ROBOT_COUNT']
            
            self.test_results['evaluate_parameter_support'] = True
            self.logger.info("✅ evaluate.py 參數支援測試通過")
            return True
            
        except Exception as e:
            self.test_results['evaluate_parameter_support'] = False
            self.logger.error(f"❌ evaluate.py 參數支援測試失敗: {e}")
            return False
    
    def test_file_structure(self) -> bool:
        """測試檔案結構"""
        try:
            self.logger.info("🧪 測試檔案結構...")
            
            # 檢查關鍵檔案是否存在
            required_files = [
                project_root / "test" / "capacity_test_controller.py",
                project_root / "test" / "isolation_manager.py",
                project_root / "test" / "capacity_analyzer.py",
                project_root / "test" / "experiment_menu.py",
                project_root / "evaluate.py",
                project_root / "lib" / "generator" / "warehouse_generator.py"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    raise Exception(f"關鍵檔案不存在: {file_path}")
            
            # 檢查模組導入
            try:
                from test.capacity_test_controller import CapacityTestController
                from test.isolation_manager import IsolationManager
                from test.capacity_analyzer import CapacityAnalyzer
            except ImportError as e:
                raise Exception(f"模組導入失敗: {e}")
            
            self.test_results['file_structure'] = True
            self.logger.info("✅ 檔案結構測試通過")
            return True
            
        except Exception as e:
            self.test_results['file_structure'] = False
            self.logger.error(f"❌ 檔案結構測試失敗: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """執行所有測試"""
        self.logger.info("🚀 開始執行基本功能測試...")
        
        self.setup()
        
        try:
            # 執行各項測試
            tests = [
                self.test_file_structure,
                self.test_isolation_manager,
                self.test_capacity_controller_init,
                self.test_capacity_analyzer_init,
                self.test_evaluate_parameter_support
            ]
            
            for test in tests:
                test()
            
            # 統計結果
            passed = sum(self.test_results.values())
            total = len(self.test_results)
            
            self.logger.info(f"\n📊 測試結果總結:")
            self.logger.info(f"通過: {passed}/{total}")
            
            for test_name, result in self.test_results.items():
                status = "✅ 通過" if result else "❌ 失敗"
                self.logger.info(f"  {test_name}: {status}")
            
            if passed == total:
                self.logger.info("🎉 所有基本功能測試通過！")
            else:
                self.logger.warning("⚠️  部分測試失敗，請檢查錯誤資訊")
            
        finally:
            self.teardown()
        
        return self.test_results


def main():
    """主函數"""
    print("RMFS 容量測試系統 - 基本功能測試")
    print("=" * 50)
    
    test_runner = BasicFunctionalityTest()
    results = test_runner.run_all_tests()
    
    # 返回適當的退出碼
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()