#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMFS 容量測試實驗選單界面

使用 rich 庫提供互動式選單，支援以下功能：
1. 系統容量壓力測試
2. 查看測試進度
3. 生成分析圖表
4. 清理臨時檔案
"""

import sys
import os
import platform
from pathlib import Path
import json
from datetime import datetime
import time
from typing import Optional, List, Dict, Any
import numpy as np

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.status import Status
except ImportError:
    print("錯誤：找不到 rich 庫，請安裝：pip install rich")
    sys.exit(1)

from test.capacity_test_controller import CapacityTestController


class ExperimentMenu:
    """RMFS 容量測試實驗選單"""
    
    def __init__(self):
        self.console = Console()
        self.controller: Optional[CapacityTestController] = None
        self.results_dir = Path(__file__).parent / "results"
        self.active_sessions = {}  # session_id -> controller
        
    def show_welcome(self):
        """顯示歡迎畫面"""
        welcome_text = Text()
        welcome_text.append("🤖 RMFS 系統容量壓力測試工具 🤖\n", style="bold blue")
        welcome_text.append("版本: 1.0.0", style="dim")
        
        panel = Panel(
            Align.center(welcome_text),
            box=box.DOUBLE,
            padding=(1, 2),
            title="歡迎",
            title_align="center"
        )
        
        self.console.print(panel)
        self.console.print()
    
    def show_main_menu(self):
        """顯示主選單"""
        menu_options = [
            "🧪 [bold green]系統容量壓力測試[/bold green] - 執行不同機器人數量的測試",
            "⚡ [bold yellow]Time-Based 參數掃描[/bold yellow] - 測試不同時間配比參數",
            "📊 [bold cyan]Queue-Based 參數掃描[/bold cyan] - 測試不同隊列閾值參數",
            "📈 [bold blue]生成容量測試圖表[/bold blue] - 分析容量測試結果",
            "📊 [bold magenta]生成基準模型圖表[/bold magenta] - 分析基準模型參數掃描結果",
            "📉 [bold magenta]時間序列分析[/bold magenta] - 分析測試的時間序列數據",
            "🧹 [bold red]清理臨時檔案[/bold red] - 清理測試產生的臨時檔案",
            "📋 [bold cyan]顯示歷史測試[/bold cyan] - 查看過往測試記錄",
            "❌ [bold dim]退出程式[/bold dim]"
        ]
        
        # 顯示活躍會話資訊
        if self.active_sessions:
            active_info = f"\n[bold yellow]活躍測試會話: {len(self.active_sessions)}[/bold yellow]"
            for session_id, controller in self.active_sessions.items():
                if controller.test_monitor:
                    status_list = controller.test_monitor.get_all_test_status()
                    running = len([s for s in status_list if s['status'] == '執行中'])
                    completed = len([s for s in status_list if s['status'] == '已完成'])
                    active_info += f"\n  • {session_id}: {running} 執行中, {completed} 已完成"
        else:
            active_info = ""
        
        self.console.print(Panel(
            "\n".join(f"{i+1}. {option}" for i, option in enumerate(menu_options)) + active_info,
            title="主選單",
            title_align="center",
            padding=(1, 2)
        ))
        
        choice = IntPrompt.ask(
            "請選擇功能",
            choices=[str(i) for i in range(1, len(menu_options) + 1)],
            default=1
        )
        
        return choice
    
    def run_capacity_test(self):
        """執行容量測試"""
        self.console.print(Panel("🧪 系統容量壓力測試", style="bold green"))
        
        # 獲取測試參數
        robot_counts = self._get_robot_counts()
        runs_per_config = self._get_runs_per_config()
        test_ticks = self._get_test_ticks()
        parallel = self._get_parallel_option()
        max_parallel = self._get_max_parallel_option(parallel)
        
        # 確認測試參數
        if not self._confirm_test_parameters_with_runs(robot_counts, runs_per_config, test_ticks, parallel, max_parallel):
            return
        
        # 初始化控制器
        self.controller = CapacityTestController()
        
        # 顯示測試開始資訊
        self.console.print(f"\n✅ 測試即將開始...")
        self.console.print(f"📊 機器人數量: {robot_counts}")
        self.console.print(f"🔄 每個配置運行次數: {runs_per_config}")
        self.console.print(f"⏱️  測試時長: {test_ticks:,} ticks")
        self.console.print(f"⚡ 並行執行: {'是' if parallel else '否'}")
        if parallel:
            self.console.print(f"🔄 最大並行數: {max_parallel}")
        
        # 執行測試
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("正在執行容量測試...", total=None)
                
                summary = self.controller.run_capacity_test(
                    robot_counts=robot_counts,
                    parallel=parallel,
                    test_ticks=test_ticks,
                    max_parallel_tests=max_parallel,
                    runs_per_config=runs_per_config
                )
            
            # 顯示測試結果
            self._show_test_summary(summary)
            
        except KeyboardInterrupt:
            self.console.print("\n❌ 測試被用戶中斷")
            if self.controller:
                self.controller.stop_all_tests()
        except Exception as e:
            self.console.print(f"\n❌ 測試執行時發生錯誤: {e}")

    def run_capacity_test_background(self):
        """在背景執行容量測試"""
        self.console.print(Panel("▶️ 背景執行容量測試", style="bold cyan"))
        
        # 獲取測試參數
        robot_counts = self._get_robot_counts()
        runs_per_config = self._get_runs_per_config()
        test_ticks = self._get_test_ticks()
        parallel = self._get_parallel_option()
        max_parallel = self._get_max_parallel_option(parallel)
        
        # 確認測試參數
        if not self._confirm_test_parameters_with_runs(robot_counts, runs_per_config, test_ticks, parallel, max_parallel):
            return
        
        # 初始化控制器（啟用監控）
        controller = CapacityTestController(enable_monitor=True)
        
        # 顯示測試開始資訊
        self.console.print(f"\n✅ 測試即將在背景開始...")
        self.console.print(f"📊 機器人數量: {robot_counts}")
        self.console.print(f"🔄 每個配置運行次數: {runs_per_config}")
        self.console.print(f"⏱️  測試時長: {test_ticks:,} ticks")
        
        try:
            # 在背景執行測試
            session_id = controller.run_capacity_test_background(
                robot_counts=robot_counts,
                parallel=parallel,
                test_ticks=test_ticks,
                max_parallel_tests=max_parallel,
                runs_per_config=runs_per_config
            )
            
            # 保存到活躍會話
            self.active_sessions[session_id] = controller
            
            self.console.print(f"\n✅ 測試已在背景開始執行")
            self.console.print(f"📌 會話ID: {session_id}")
            self.console.print("💡 提示: 選擇 '監控進行中測試' 來查看進度")
            
        except Exception as e:
            self.console.print(f"\n❌ 啟動背景測試時發生錯誤: {e}")
    
    def monitor_active_tests(self):
        """監控進行中的測試"""
        if not self.active_sessions:
            self.console.print(Panel("沒有進行中的測試會話", style="yellow"))
            return
        
        # 選擇要監控的會話
        session_choices = list(self.active_sessions.keys())
        
        if len(session_choices) == 1:
            selected_session = session_choices[0]
        else:
            self.console.print("\n選擇要監控的測試會話:")
            for i, session_id in enumerate(session_choices):
                controller = self.active_sessions[session_id]
                if controller.test_monitor:
                    status_list = controller.test_monitor.get_all_test_status()
                    running = len([s for s in status_list if s['status'] == '執行中'])
                    completed = len([s for s in status_list if s['status'] == '已完成'])
                    self.console.print(f"{i+1}. {session_id} - {running} 執行中, {completed} 已完成")
            
            choice = IntPrompt.ask(
                "選擇會話",
                choices=[str(i+1) for i in range(len(session_choices))],
                default=1
            ) - 1
            selected_session = session_choices[choice]
        
        controller = self.active_sessions[selected_session]
        
        if not controller.test_monitor:
            self.console.print("該會話未啟用監控功能")
            return
        
        # 實時監控循環
        with Live(console=self.console, refresh_per_second=1) as live:
            while True:
                try:
                    # 獲取所有測試狀態
                    status_list = controller.test_monitor.get_all_test_status()
                    
                    # 創建監控表格
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("機器人數量", justify="center")
                    table.add_column("運行", justify="center")
                    table.add_column("狀態", justify="center")
                    table.add_column("進度", justify="center")
                    table.add_column("完成訂單", justify="center")
                    table.add_column("執行時間", justify="right")
                    
                    for status in status_list:
                        # 狀態顏色
                        status_color = {
                            "執行中": "yellow",
                            "已完成": "green",
                            "失敗": "red",
                            "已取消": "dim"
                        }.get(status['status'], "white")
                        
                        # 進度條
                        progress = status['progress']['percentage']
                        progress_bar = self._create_progress_bar(progress)
                        
                        table.add_row(
                            str(status['robot_count']),
                            f"第 {status['run_index'] + 1} 次",
                            f"[{status_color}]{status['status']}[/{status_color}]",
                            f"{progress_bar} {progress:.1f}%",
                            f"{status['progress']['completed_orders']}/{status['progress']['total_orders']}",
                            f"{status['elapsed_time']:.1f}s"
                        )
                    
                    # 創建輸出面板
                    output_panel = self._create_output_panel(controller, status_list)
                    
                    # 更新顯示
                    display = Panel(
                        table,
                        title=f"測試監控 - 會話 {selected_session}",
                        subtitle="按 q 返回主選單, s 查看詳細輸出"
                    )
                    
                    live.update(display)
                    
                    # 檢查鍵盤輸入（跨平台方案）
                    try:
                        if platform.system() == "Windows":
                            # Windows 平台使用 msvcrt
                            import msvcrt
                            if msvcrt.kbhit():
                                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                                if key == 'q':
                                    break
                                elif key == 's':
                                    # 顯示詳細輸出
                                    self._show_test_output(controller, status_list)
                        else:
                            # Unix/Linux 平台使用 termios
                            import select
                            import termios
                            import tty
                            
                            old_settings = termios.tcgetattr(sys.stdin)
                            try:
                                tty.setcbreak(sys.stdin.fileno())
                                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                                    key = sys.stdin.read(1)
                                    if key.lower() == 'q':
                                        break
                                    elif key.lower() == 's':
                                        # 顯示詳細輸出
                                        self._show_test_output(controller, status_list)
                            finally:
                                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    except Exception:
                        # 如果鍵盤輸入檢測失敗，繼續運行
                        pass
                    
                    # 檢查是否所有測試都已完成
                    if all(s['status'] in ['已完成', '失敗', '已取消'] for s in status_list):
                        self.console.print("\n✅ 所有測試已完成")
                        break
                    
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    if Confirm.ask("\n確定要返回主選單？", default=True):
                        break
                except Exception as e:
                    self.console.print(f"\n❌ 監控時發生錯誤: {e}")
                    break
    
    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """創建進度條"""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{'green' if percentage == 100 else 'yellow'}]{bar}[/]"
    
    def _create_output_panel(self, controller: CapacityTestController, 
                           status_list: List[Dict]) -> Panel:
        """創建輸出面板"""
        # 找出最新的執行中測試
        running_tests = [s for s in status_list if s['status'] == '執行中']
        if not running_tests:
            return Panel("沒有執行中的測試", style="dim")
        
        # 獲取最新測試的輸出
        latest_test = running_tests[0]
        test_id = latest_test['test_id']
        
        stdout_lines, stderr_lines = controller.test_monitor.get_test_output(test_id, max_lines=10)
        
        output_text = ""
        if stdout_lines:
            output_text += "[bold]最新輸出:[/bold]\n"
            output_text += "\n".join(stdout_lines[-5:])  # 顯示最後5行
        
        if stderr_lines:
            output_text += "\n\n[bold red]錯誤輸出:[/bold red]\n"
            output_text += "\n".join(stderr_lines[-3:])  # 顯示最後3行
        
        return Panel(output_text or "等待輸出...", title=f"測試 {test_id}")
    
    def _show_test_output(self, controller: CapacityTestController, 
                         status_list: List[Dict]):
        """顯示測試的詳細輸出"""
        # 選擇要查看的測試
        test_choices = [(s['test_id'], s['robot_count'], s['run_index']) 
                       for s in status_list]
        
        if not test_choices:
            return
        
        self.console.clear()
        self.console.print("\n選擇要查看詳細輸出的測試:")
        
        for i, (test_id, robot_count, run_index) in enumerate(test_choices):
            self.console.print(f"{i+1}. 機器人 {robot_count} - 第 {run_index+1} 次運行")
        
        choice = IntPrompt.ask(
            "選擇測試",
            choices=[str(i+1) for i in range(len(test_choices))],
            default=1
        ) - 1
        
        selected_test_id = test_choices[choice][0]
        
        # 獲取輸出
        stdout_lines, stderr_lines = controller.test_monitor.get_test_output(
            selected_test_id, max_lines=100
        )
        
        # 顯示輸出
        self.console.print(f"\n測試 {selected_test_id} 的詳細輸出:")
        
        if stdout_lines:
            self.console.print("\n[bold]標準輸出:[/bold]")
            for line in stdout_lines:
                self.console.print(line)
        
        if stderr_lines:
            self.console.print("\n[bold red]錯誤輸出:[/bold red]")
            for line in stderr_lines:
                self.console.print(f"[red]{line}[/red]")
        
        Prompt.ask("\n按 Enter 返回監控畫面", default="")
    
    def _get_robot_counts(self) -> List[int]:
        """獲取要測試的機器人數量"""
        self.console.print("\n📊 請設定要測試的機器人數量:")
        
        use_default = Confirm.ask("使用預設數量 [25, 30]？", default=True)
        
        if use_default:
            return [25, 30]
        
        robot_counts = []
        self.console.print("請輸入機器人數量（輸入 0 結束）:")
        
        while True:
            count = IntPrompt.ask("機器人數量", default=0)
            if count == 0:
                break
            if count < 1:
                self.console.print("❌ 機器人數量必須大於 0")
                continue
            if count in robot_counts:
                self.console.print(f"⚠️  數量 {count} 已經存在")
                continue
            
            robot_counts.append(count)
            self.console.print(f"✅ 已加入: {count}")
        
        if not robot_counts:
            self.console.print("⚠️  未設定任何數量，使用預設值")
            return [25, 30]
        
        robot_counts.sort()
        return robot_counts
    
    def _get_test_ticks(self) -> int:
        """獲取測試 tick 數"""
        self.console.print("\n⏱️  請設定測試時長:")
        
        options = {
            "1": ("快速測試", 10000),
            "2": ("標準測試", 50000), 
            "3": ("長時間測試", 100000),
            "4": ("超長測試", 200000),
            "5": ("自訂數量", 0)
        }
        
        for key, (desc, ticks) in options.items():
            if ticks > 0:
                self.console.print(f"{key}. {desc} ({ticks:,} ticks)")
            else:
                self.console.print(f"{key}. {desc}")
        
        choice = Prompt.ask("請選擇", choices=list(options.keys()), default="3")
        
        if choice == "5":
            return IntPrompt.ask("請輸入 tick 數", default=100000, show_default=True)
        else:
            return options[choice][1]
    
    def _get_parallel_option(self) -> bool:
        """獲取是否並行執行"""
        return Confirm.ask("\n⚡ 是否並行執行測試？", default=True)
    
    def _get_max_parallel_option(self, parallel: bool) -> Optional[int]:
        """獲取最大並行數量"""
        if not parallel:
            return 1
        
        cpu_count = os.cpu_count() or 4
        default_parallel = max(1, cpu_count // 2)
        
        use_auto = Confirm.ask(
            f"🔄 使用自動並行數量 ({default_parallel})？", 
            default=True
        )
        
        if use_auto:
            return default_parallel
        
        return IntPrompt.ask(
            "請輸入最大並行測試數量",
            default=default_parallel,
            show_default=True
        )
    
    def _confirm_test_parameters(self, robot_counts: List[int], test_ticks: int, 
                               parallel: bool, max_parallel: Optional[int]) -> bool:
        """確認測試參數"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("參數", style="dim", width=20)
        table.add_column("值", style="bold")
        
        table.add_row("機器人數量", str(robot_counts))
        table.add_row("測試時長", f"{test_ticks:,} ticks")
        table.add_row("並行執行", "是" if parallel else "否")
        if parallel:
            table.add_row("最大並行數", str(max_parallel))
        
        # 估算執行時間
        estimated_time = self._estimate_execution_time(len(robot_counts), test_ticks, parallel, max_parallel)
        table.add_row("預估執行時間", estimated_time)
        
        self.console.print("\n📋 測試參數確認:")
        self.console.print(table)
        
        return Confirm.ask("\n✅ 確認開始測試？", default=True)

    def _get_runs_per_config(self) -> int:
        """獲取每個配置的運行次數"""
        self.console.print("\n🔄 請設定每個機器人配置的運行次數:")
        
        runs = IntPrompt.ask(
            "每個配置運行次數", 
            default=1,
            show_default=True
        )
        
        if runs < 1:
            self.console.print("⚠️  運行次數必須至少為 1，使用預設值 1")
            return 1
        
        if runs > 10:
            confirm = Confirm.ask(f"⚠️  您設定了 {runs} 次運行，這可能需要很長時間。確定繼續？", default=False)
            if not confirm:
                return self._get_runs_per_config()
        
        return runs
    
    def _confirm_test_parameters_with_runs(self, robot_counts: List[int], runs_per_config: int,
                                         test_ticks: int, parallel: bool, max_parallel: Optional[int]) -> bool:
        """確認測試參數（包含運行次數）"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("參數", style="dim", width=20)
        table.add_column("值", style="bold")
        
        table.add_row("機器人數量", str(robot_counts))
        table.add_row("每個配置運行次數", str(runs_per_config))
        table.add_row("總測試數", str(len(robot_counts) * runs_per_config))
        table.add_row("測試時長", f"{test_ticks:,} ticks")
        table.add_row("並行執行", "是" if parallel else "否")
        if parallel:
            table.add_row("最大並行數", str(max_parallel))
        
        # 估算執行時間
        total_tests = len(robot_counts) * runs_per_config
        estimated_time = self._estimate_execution_time(total_tests, test_ticks, parallel, max_parallel)
        table.add_row("預估執行時間", estimated_time)
        
        self.console.print("\n📋 測試參數確認:")
        self.console.print(table)
        
        return Confirm.ask("\n✅ 確認開始測試？", default=True)
    
    def _estimate_execution_time(self, num_tests: int, test_ticks: int, 
                               parallel: bool, max_parallel: Optional[int]) -> str:
        """估算執行時間"""
        # 基於經驗的時間估算：每 1000 ticks 約需 1-2 秒
        seconds_per_1k_ticks = 1.5
        base_time_per_test = (test_ticks / 1000) * seconds_per_1k_ticks
        
        if parallel and max_parallel:
            total_time = (num_tests / max_parallel) * base_time_per_test
        else:
            total_time = num_tests * base_time_per_test
        
        if total_time < 60:
            return f"{total_time:.0f} 秒"
        elif total_time < 3600:
            return f"{total_time/60:.1f} 分鐘"
        else:
            return f"{total_time/3600:.1f} 小時"
    
    def _show_test_summary(self, summary: Dict[str, Any]):
        """顯示測試摘要"""
        self.console.print("\n" + "="*60)
        self.console.print("🎉 測試完成！", style="bold green")
        
        # 基本統計
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("項目", style="dim")
        table.add_column("值", style="bold")
        
        table.add_row("總測試數", str(summary['total_tests']))
        table.add_row("成功測試", str(summary['completed_tests']))
        table.add_row("失敗測試", str(summary['failed_tests']))
        table.add_row("執行時間", f"{summary['total_execution_time']:.1f} 秒")
        
        # 如果有 runs_per_config，顯示它
        if 'runs_per_config' in summary:
            table.add_row("每個配置運行次數", str(summary['runs_per_config']))
        
        self.console.print(table)
        
        # 顯示各個測試的結果
        if 'results_by_robot_count' in summary:
            # 使用新的分組結果格式
            result_table = Table(show_header=True, header_style="bold yellow")
            result_table.add_column("機器人數量", justify="center")
            result_table.add_column("成功/總數", justify="center")
            result_table.add_column("平均執行時間", justify="right")
            result_table.add_column("狀態", justify="center")
            
            for robot_count in sorted(summary['results_by_robot_count'].keys()):
                results = summary['results_by_robot_count'][robot_count]
                completed = len([r for r in results if r['status'] == 'completed'])
                total = len(results)
                avg_time = sum(r.get('execution_time', 0) for r in results) / total if total > 0 else 0
                
                status_style = "green" if completed == total else ("yellow" if completed > 0 else "red")
                status_text = "✓ 全部成功" if completed == total else (f"⚠ 部分成功" if completed > 0 else "✗ 全部失敗")
                
                result_table.add_row(
                    str(robot_count),
                    f"{completed}/{total}",
                    f"{avg_time:.1f}s",
                    f"[{status_style}]{status_text}[/{status_style}]"
                )
            
            self.console.print("\n📊 詳細結果:")
            self.console.print(result_table)
        elif summary['results']:
            # 舊的單一結果格式（向後兼容）
            result_table = Table(show_header=True, header_style="bold yellow")
            result_table.add_column("機器人數量", justify="center")
            result_table.add_column("運行", justify="center")
            result_table.add_column("狀態", justify="center")
            result_table.add_column("執行時間", justify="right")
            
            for result in summary['results']:
                status_style = "green" if result['status'] == 'completed' else "red"
                run_index = result.get('run_index', 0)
                result_table.add_row(
                    str(result['robot_count']),
                    f"第 {run_index + 1} 次",
                    f"[{status_style}]{result['status']}[/{status_style}]",
                    f"{result.get('execution_time', 0):.1f}s"
                )
            
            self.console.print("\n📊 詳細結果:")
            self.console.print(result_table)
        
        # 顯示輸出目錄
        output_dir = self.controller.base_output_dir if self.controller else summary.get('output_dir', 'N/A')
        self.console.print(f"\n📁 結果保存在: {output_dir}")
        self.console.print("="*60)
    
    def show_test_progress(self):
        """顯示測試進度"""
        self.console.print(Panel("📊 測試進度查看", style="bold yellow"))
        
        if not self.controller:
            self.console.print("❌ 沒有正在運行的測試")
            return
        
        progress_info = self.controller.get_test_progress()
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("狀態", style="dim")
        table.add_column("數量", justify="center")
        table.add_column("詳細", style="dim")
        
        table.add_row("正在執行", str(progress_info['running_tests']), 
                     ", ".join(progress_info['running_test_details']))
        table.add_row("已完成", str(progress_info['completed_tests']),
                     ", ".join(progress_info['completed_test_details']))
        table.add_row("失敗", str(progress_info['failed_tests']),
                     ", ".join(progress_info['failed_test_details']))
        
        self.console.print(table)
    
    def generate_analysis(self):
        """生成分析圖表"""
        self.console.print(Panel("📈 生成分析圖表", style="bold blue"))
        
        # 尋找結果目錄
        if not self.results_dir.exists():
            self.console.print("❌ 找不到測試結果目錄")
            return
        
        # 列出可用的測試結果
        test_dirs = [d for d in self.results_dir.iterdir() if d.is_dir()]
        
        if not test_dirs:
            self.console.print("❌ 找不到任何測試結果")
            return
        
        # 讓用戶選擇要分析的結果
        self.console.print("可用的測試結果:")
        for i, test_dir in enumerate(test_dirs, 1):
            self.console.print(f"{i}. {test_dir.name}")
        
        choice = IntPrompt.ask(
            "請選擇要分析的測試結果",
            choices=[str(i) for i in range(1, len(test_dirs) + 1)],
            default=1
        )
        
        selected_dir = test_dirs[choice - 1]
        
        try:
            from test.capacity_analyzer import CapacityAnalyzer
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("正在生成分析報告...", total=None)
                
                analyzer = CapacityAnalyzer(selected_dir)
                report_path = analyzer.generate_analysis_report()
            
            self.console.print(f"✅ 分析報告已生成: {report_path}")
            
        except ImportError:
            self.console.print("❌ 找不到 CapacityAnalyzer，請確保已實作 capacity_analyzer.py")
        except Exception as e:
            self.console.print(f"❌ 生成分析報告時發生錯誤: {e}")
    
    def cleanup_files(self):
        """清理臨時檔案"""
        self.console.print(Panel("🧹 清理臨時檔案", style="bold red"))
        
        keep_results = Confirm.ask("是否保留結果檔案？", default=True)
        
        if self.controller:
            cleaned_count = self.controller.cleanup_test_files(keep_results)
            self.console.print(f"✅ 已清理 {cleaned_count} 個工作空間")
        else:
            self.console.print("⚠️  沒有控制器實例，無法清理檔案")
    
    def show_history(self):
        """顯示歷史測試"""
        self.console.print(Panel("📋 歷史測試記錄", style="bold cyan"))
        
        if not self.results_dir.exists():
            self.console.print("❌ 找不到測試結果目錄")
            return
        
        # 尋找所有測試摘要檔案
        summary_files = list(self.results_dir.rglob("capacity_test_summary.json"))
        
        if not summary_files:
            self.console.print("❌ 找不到任何歷史測試記錄")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("測試ID", style="dim")
        table.add_column("開始時間", style="dim")
        table.add_column("機器人數量", justify="center")
        table.add_column("成功/總數", justify="center")
        table.add_column("執行時間", justify="right")
        
        for summary_file in summary_files:
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                start_time = datetime.fromisoformat(summary['start_time']).strftime("%Y-%m-%d %H:%M")
                robot_counts = str(summary.get('robot_counts_tested', []))
                success_rate = f"{summary['completed_tests']}/{summary['total_tests']}"
                exec_time = f"{summary['total_execution_time']:.1f}s"
                
                table.add_row(
                    summary['test_session_id'][:8],
                    start_time,
                    robot_counts,
                    success_rate,
                    exec_time
                )
                
            except Exception as e:
                self.console.print(f"⚠️  讀取 {summary_file} 時發生錯誤: {e}")
        
        self.console.print(table)
    
    def run_time_based_optimization(self):
        """執行 Time-Based 控制器參數掃描"""
        self.console.print(Panel("⚡ Time-Based 參數掃描", style="bold yellow"))
        
        # 測試參數設定
        robot_counts = [25, 30]
        time_ratios = ["50:50", "60:40", "65:35", "70:30", "75:25", "80:20"]
        runs_per_config = self._get_runs_per_config()
        test_ticks = self._get_test_ticks()
        parallel = self._get_parallel_option()
        max_parallel = self._get_max_parallel_option(parallel)
        
        # 顯示測試配置
        self.console.print("\n📋 測試配置:")
        self.console.print(f"機器人數量: {robot_counts}")
        self.console.print(f"時間配比: {time_ratios}")
        self.console.print(f"每個組合運行次數: {runs_per_config}")
        self.console.print(f"測試時長: {test_ticks:,} ticks")
        
        total_tests = len(robot_counts) * len(time_ratios) * runs_per_config
        self.console.print(f"\n總測試數: {total_tests}")
        
        # 確認開始
        if not Confirm.ask("\n✅ 確認開始測試？", default=True):
            return
        
        # 準備測試
        from test.baseline_test_controller import BaselineTestController
        controller = BaselineTestController()
        
        try:
            # 執行測試
            summary = controller.run_time_based_sweep(
                robot_counts=robot_counts,
                time_ratios=time_ratios,
                runs_per_config=runs_per_config,
                test_ticks=test_ticks,
                parallel=parallel,  # 使用用戶選擇的並行設置
                max_parallel=max_parallel
            )
            
            # 顯示結果摘要
            self._show_baseline_test_summary(summary, "Time-Based")
            
        except KeyboardInterrupt:
            self.console.print("\n❌ 測試被用戶中斷")
        except Exception as e:
            self.console.print(f"\n❌ 測試執行時發生錯誤: {e}")
    
    def run_queue_based_optimization(self):
        """執行 Queue-Based 控制器參數掃描"""
        self.console.print(Panel("📊 Queue-Based 參數掃描", style="bold cyan"))
        
        # 測試參數設定
        robot_counts = [25, 30]
        queue_thresholds = [2, 3, 4, 5, 6]
        runs_per_config = self._get_runs_per_config()
        test_ticks = self._get_test_ticks()
        parallel = self._get_parallel_option()
        max_parallel = self._get_max_parallel_option(parallel)
        
        # 顯示測試配置
        self.console.print("\n📋 測試配置:")
        self.console.print(f"機器人數量: {robot_counts}")
        self.console.print(f"隊列閾值: {queue_thresholds}")
        self.console.print(f"每個組合運行次數: {runs_per_config}")
        self.console.print(f"測試時長: {test_ticks:,} ticks")
        
        total_tests = len(robot_counts) * len(queue_thresholds) * runs_per_config
        self.console.print(f"\n總測試數: {total_tests}")
        
        # 確認開始
        if not Confirm.ask("\n✅ 確認開始測試？", default=True):
            return
        
        # 準備測試
        from test.baseline_test_controller import BaselineTestController
        controller = BaselineTestController()
        
        try:
            # 執行測試
            summary = controller.run_queue_based_sweep(
                robot_counts=robot_counts,
                queue_thresholds=queue_thresholds,
                runs_per_config=runs_per_config,
                test_ticks=test_ticks,
                parallel=parallel,  # 使用用戶選擇的並行設置
                max_parallel=max_parallel
            )
            
            # 顯示結果摘要
            self._show_baseline_test_summary(summary, "Queue-Based")
            
        except KeyboardInterrupt:
            self.console.print("\n❌ 測試被用戶中斷")
        except Exception as e:
            self.console.print(f"\n❌ 測試執行時發生錯誤: {e}")
    
    def generate_baseline_analysis(self):
        """生成基準模型參數掃描的分析圖表"""
        self.console.print(Panel("📊 生成基準模型分析圖表", style="bold magenta"))
        
        # 尋找基準模型測試結果
        baseline_dir = Path(__file__).parent / "results"
        if not baseline_dir.exists():
            self.console.print("❌ 找不到基準模型測試結果目錄")
            return
        
        # 搜尋所有基準測試目錄
        # 支援新舊命名規則：
        # - 新：queue_based_*、time_based_*
        # - 舊：baseline_* 或包含 time_based/、queue_based 子資料夾
        baseline_test_dirs = [
            d for d in baseline_dir.iterdir()
            if d.is_dir() and (
                d.name.startswith(("baseline_", "queue_based_", "time_based_"))
                or (d / "time_based").exists()
                or (d / "queue_based").exists()
            )
        ]
        
        if not baseline_test_dirs:
            self.console.print("❌ 找不到任何基準模型測試結果")
            return
        
        # 按時間排序（最新的在前）
        baseline_test_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 分析每個測試目錄，判斷其類型
        categorized_tests = {"time_based": [], "queue_based": []}
        
        for test_dir in baseline_test_dirs:
            name = test_dir.name
            # 先用資料夾名判斷
            if name.startswith("time_based_") or name.startswith("tb_"):
                categorized_tests["time_based"].append(test_dir)
                continue
            if name.startswith("queue_based_") or name.startswith("qb_"):
                categorized_tests["queue_based"].append(test_dir)
                continue
            if name.startswith("baseline_"):
                # baseline_ 可能同時包含兩種，往下探測
                pass
            
            # 其次用子資料夾探測
            if (test_dir / "time_based").exists():
                categorized_tests["time_based"].append(test_dir)
            if (test_dir / "queue_based").exists():
                categorized_tests["queue_based"].append(test_dir)
            
            # 最後檢查直接子資料夾命名（舊格式）
            subdirs = [d for d in test_dir.iterdir() if d.is_dir()]
            if subdirs:
                for sub in subdirs:
                    if sub.name.startswith(("tb_", "time_based_")):
                        categorized_tests["time_based"].append(test_dir)
                        break
                    if sub.name.startswith(("qb_", "queue_based_")):
                        categorized_tests["queue_based"].append(test_dir)
                        break
        
        # 列出可用的測試類型
        test_types = []
        if categorized_tests["time_based"]:
            test_types.append("time_based")
        if categorized_tests["queue_based"]:
            test_types.append("queue_based")
        
        if not test_types:
            self.console.print("❌ 找不到任何有效的基準模型測試結果")
            return
        
        # 選擇測試類型
        if len(test_types) == 1:
            selected_type = test_types[0]
        else:
            self.console.print("\n選擇要分析的測試類型:")
            for i, test_type in enumerate(test_types, 1):
                display_name = "Time-Based" if test_type == "time_based" else "Queue-Based"
                count = len(categorized_tests[test_type])
                self.console.print(f"{i}. {display_name} ({count} 個測試)")
            
            choice = IntPrompt.ask(
                "請選擇",
                choices=[str(i) for i in range(1, len(test_types) + 1)],
                default=1
            )
            selected_type = test_types[choice - 1]
        
        # 列出該類型的測試結果
        available_tests = categorized_tests[selected_type]
        
        # 顯示可選擇的測試結果（只顯示匹配類型且存在實際結果的）
        filtered_tests: List[Path] = []
        for d in available_tests:
            if selected_type == "time_based":
                if d.name.startswith(("time_based_", "tb_")) or (d / "time_based").exists():
                    filtered_tests.append(d)
            else:
                if d.name.startswith(("queue_based_", "qb_")) or (d / "queue_based").exists():
                    filtered_tests.append(d)

        # 回退：若過濾後為空，仍使用原列表（避免過度嚴格造成空）
        if not filtered_tests:
            filtered_tests = available_tests

        self.console.print(f"\n可用的 {selected_type} 測試結果:")
        for i, test_dir in enumerate(filtered_tests[:10], 1):  # 只顯示最新的10個
            timestamp = datetime.fromtimestamp(test_dir.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.console.print(f"{i}. {test_dir.name} ({timestamp})")
        
        choice = IntPrompt.ask(
            "請選擇要分析的測試結果",
            choices=[str(i) for i in range(1, min(11, len(filtered_tests) + 1))],
            default=1
        )
        
        selected_test_dir = filtered_tests[choice - 1]
        
        # 分析器應該使用包含 workspaces 的目錄
        analysis_dir = selected_test_dir
        
        try:
            from test.baseline_analyzer import BaselineAnalyzer
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("正在生成分析報告...", total=None)
                
                analyzer = BaselineAnalyzer(analysis_dir)
                results = analyzer.generate_all_analyses()
                
                # 顯示所有生成的文件路徑
                for analysis_type, path in results.items():
                    if path:
                        self.console.print(f"✅ {analysis_type}: {path}")
            
        except ImportError:
            self.console.print("❌ 找不到 BaselineAnalyzer，請確保已實作 baseline_analyzer.py")
        except Exception as e:
            self.console.print(f"❌ 生成分析報告時發生錯誤: {e}")
    
    def _show_baseline_test_summary(self, summary: Dict[str, Any], test_type: str):
        """顯示基準模型測試摘要"""
        self.console.print("\n" + "="*60)
        self.console.print(f"🎉 {test_type} 參數掃描完成！", style="bold green")
        
        # 基本統計
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("項目", style="dim")
        table.add_column("值", style="bold")
        
        table.add_row("總測試數", str(summary['total_tests']))
        table.add_row("成功測試", str(summary['completed_tests']))
        table.add_row("失敗測試", str(summary['failed_tests']))
        table.add_row("執行時間", f"{summary['total_execution_time']:.1f} 秒")
        
        self.console.print(table)
        
        # 顯示各參數的測試結果
        if 'results_by_parameter' in summary:
            result_table = Table(show_header=True, header_style="bold yellow")
            result_table.add_column("機器人數量", justify="center")
            result_table.add_column("參數值", justify="center")
            result_table.add_column("成功/總數", justify="center")
            result_table.add_column("平均完成率", justify="right")
            result_table.add_column("平均等待時間", justify="right")
            
            for key, results in sorted(summary['results_by_parameter'].items()):
                robot_count, param_value = key
                completed = len([r for r in results if r['status'] == 'completed'])
                total = len(results)
                
                # 計算平均指標
                if completed > 0:
                    avg_completion = np.mean([r.get('completion_rate', 0) for r in results if r['status'] == 'completed'])
                    avg_wait = np.mean([r.get('avg_wait_time', 0) for r in results if r['status'] == 'completed'])
                else:
                    avg_completion = 0
                    avg_wait = 0
                
                result_table.add_row(
                    str(robot_count),
                    str(param_value),
                    f"{completed}/{total}",
                    f"{avg_completion:.1%}",
                    f"{avg_wait:.1f}s"
                )
            
            self.console.print("\n📊 參數測試結果:")
            self.console.print(result_table)
        
        # 顯示輸出目錄
        self.console.print(f"\n📁 結果保存在: {summary.get('output_dir', 'N/A')}")
        self.console.print("💡 提示: 使用「生成基準模型圖表」來分析詳細結果")
        self.console.print("="*60)

    def analyze_time_series(self):
        """執行時間序列分析"""
        self.console.print(Panel(
            "[bold yellow]時間序列分析[/bold yellow]\n"
            "分析測試過程中的時間序列數據，包括訂單完成進度、完成率變化等",
            title="功能說明",
            padding=(1, 2)
        ))
        
        # 列出可分析的測試結果
        results = []
        for result_dir in self.results_dir.iterdir():
            if result_dir.is_dir() and result_dir.name.startswith("capacity_test_"):
                # 檢查是否有 workspaces 目錄
                workspaces_dir = result_dir / "workspaces"
                if workspaces_dir.exists():
                    # 計算有多少個測試
                    test_count = len(list(workspaces_dir.iterdir()))
                    if test_count > 0:
                        results.append({
                            'path': result_dir,
                            'name': result_dir.name,
                            'timestamp': result_dir.name.split('_')[2] + '_' + result_dir.name.split('_')[3],
                            'test_count': test_count
                        })
        
        if not results:
            self.console.print("[yellow]沒有找到可分析的測試結果[/yellow]")
            return
        
        # 按時間排序（最新的在前）
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 顯示可選擇的結果
        self.console.print("\n[bold]可分析的測試結果：[/bold]")
        for i, result in enumerate(results[:10]):  # 只顯示最新的10個
            timestamp = result['timestamp']
            formatted_time = f"{timestamp[:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
            self.console.print(
                f"{i+1}. {formatted_time} - {result['test_count']} 個測試"
            )
        
        # 讓用戶選擇
        choice = IntPrompt.ask(
            "請選擇要分析的測試結果",
            choices=[str(i+1) for i in range(min(10, len(results)))],
            default=1
        )
        
        selected_result = results[choice - 1]
        
        with Status("正在分析時間序列數據...", console=self.console):
            try:
                # 執行分析腳本
                import subprocess
                import sys
                
                result = subprocess.run(
                    [sys.executable, "test/analyze_time_series.py", str(selected_result['path'])],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.console.print("[green]✓ 分析完成！[/green]")
                    
                    # 顯示生成的文件
                    report_file = selected_result['path'] / 'time_series_report.md'
                    chart_file = selected_result['path'] / 'time_series_analysis.png'
                    
                    if report_file.exists():
                        self.console.print(f"\n📄 報告文件: {report_file}")
                        # 讀取並顯示報告摘要
                        with open(report_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 只顯示表格部分
                            if "測試摘要" in content:
                                summary = content.split("測試摘要")[1].split("\n\n")[0]
                                self.console.print(Panel(
                                    "測試摘要" + summary,
                                    title="分析結果",
                                    padding=(1, 2)
                                ))
                    
                    if chart_file.exists():
                        self.console.print(f"📊 圖表文件: {chart_file}")
                        self.console.print("\n[dim]提示: 圖表已保存，可使用圖片檢視器開啟查看[/dim]")
                    
                else:
                    self.console.print(f"[red]✗ 分析失敗: {result.stderr}[/red]")
                    
            except Exception as e:
                self.console.print(f"[red]✗ 執行分析時發生錯誤: {e}[/red]")

    def run(self):
        """運行主程式"""
        self.show_welcome()
        
        try:
            while True:
                choice = self.show_main_menu()
                
                if choice == 1:
                    self.run_capacity_test()
                elif choice == 2:
                    self.run_time_based_optimization()
                elif choice == 3:
                    self.run_queue_based_optimization()
                elif choice == 4:
                    self.generate_analysis()
                elif choice == 5:
                    self.generate_baseline_analysis()
                elif choice == 6:
                    self.analyze_time_series()
                elif choice == 7:
                    self.cleanup_files()
                elif choice == 8:
                    self.show_history()
                elif choice == 9:
                    self.console.print("👋 再見！")
                    # 清理所有活躍會話
                    for controller in self.active_sessions.values():
                        if controller.test_monitor:
                            controller.test_monitor.cleanup()
                    break
                
                # 暫停以便用戶查看結果
                if choice != 7:
                    self.console.print()
                    Prompt.ask("按 Enter 繼續", default="")
                    self.console.clear()
                    
        except KeyboardInterrupt:
            self.console.print("\n👋 程式被用戶中斷，再見！")
            # 清理所有活躍會話
            for controller in self.active_sessions.values():
                if controller.test_monitor:
                    controller.test_monitor.cleanup()
        except Exception as e:
            self.console.print(f"\n❌ 程式執行時發生錯誤: {e}")


def main():
    """主函數"""
    menu = ExperimentMenu()
    menu.run()


if __name__ == '__main__':
    main()