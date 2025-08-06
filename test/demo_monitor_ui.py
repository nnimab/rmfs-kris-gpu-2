#!/usr/bin/env python3
"""
演示監控UI功能
顯示如何使用 rich 庫創建實時監控介面
"""
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_demo_status_table():
    """創建演示狀態表格"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("機器人數量", justify="center")
    table.add_column("運行", justify="center")
    table.add_column("狀態", justify="center")
    table.add_column("進度", justify="center", width=30)
    table.add_column("完成訂單", justify="center")
    table.add_column("執行時間", justify="right")
    
    # 模擬資料
    test_data = [
        (20, 1, "執行中", 45.2, 23, 50, 67.3),
        (20, 2, "執行中", 32.8, 16, 50, 49.1),
        (25, 1, "已完成", 100.0, 50, 50, 150.2),
        (25, 2, "執行中", 78.5, 39, 50, 117.8),
        (30, 1, "待執行", 0.0, 0, 50, 0.0),
    ]
    
    for robot_count, run_idx, status, progress, completed, total, elapsed in test_data:
        # 狀態顏色
        status_color = {
            "執行中": "yellow",
            "已完成": "green",
            "失敗": "red",
            "待執行": "dim"
        }.get(status, "white")
        
        # 進度條
        filled = int(20 * progress / 100)
        progress_bar = "█" * filled + "░" * (20 - filled)
        progress_text = f"[{'green' if progress == 100 else 'yellow'}]{progress_bar}[/] {progress:.1f}%"
        
        table.add_row(
            str(robot_count),
            f"第 {run_idx} 次",
            f"[{status_color}]{status}[/{status_color}]",
            progress_text,
            f"{completed}/{total}",
            f"{elapsed:.1f}s"
        )
    
    return table


def create_demo_output_panel():
    """創建演示輸出面板"""
    output_text = """[bold]最新輸出:[/bold]
進度: 2260/5000 ticks, 完成訂單: 23/50
[INFO] 機器人 R-001 開始執行訂單 #024
[INFO] 機器人 R-005 到達貨架 P-127
[INFO] 路口 I-23 切換信號: NS -> EW
[INFO] 訂單 #023 已完成，耗時: 425.3 秒"""
    
    return Panel(output_text, title="測試 robots_20_run0_abc12345", border_style="blue")


def demo_monitor_ui():
    """演示監控UI"""
    console = Console()
    
    console.print("\n" + "=" * 60)
    console.print("📊 測試監控介面演示", style="bold cyan")
    console.print("=" * 60)
    console.print("\n這是監控介面的演示，顯示實時測試進度和輸出")
    console.print("在實際使用中，資料會即時更新\n")
    
    # 創建佈局
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=4)
    )
    
    # 設置標題
    layout["header"].update(Panel("🔍 容量測試監控 - 會話 abc12345", style="bold"))
    
    # 主要內容區域分為表格和輸出
    layout["main"].split_row(
        Layout(create_demo_status_table(), name="table"),
        Layout(create_demo_output_panel(), name="output", ratio=1)
    )
    
    # 設置底部說明
    layout["footer"].update(
        Panel(
            "[bold yellow]操作說明:[/bold yellow]\n"
            "• 按 [bold]q[/bold] 返回主選單\n"
            "• 按 [bold]s[/bold] 查看詳細輸出\n"
            "• 按 [bold]c[/bold] 取消選中的測試",
            style="dim"
        )
    )
    
    # 顯示靜態演示
    console.print(layout)
    
    console.print("\n[dim]這是靜態演示。在實際運行時，表格和輸出會實時更新。[/dim]")
    console.print("[dim]選單系統支援背景執行測試，您可以繼續使用其他功能。[/dim]\n")


def demo_progress_animation():
    """演示進度動畫"""
    console = Console()
    
    console.print("\n演示實時進度更新:")
    
    with Live(console=console, refresh_per_second=4) as live:
        for i in range(101):
            # 創建進度表格
            table = Table(show_header=True, header_style="bold")
            table.add_column("測試項目")
            table.add_column("進度", width=40)
            
            # 添加進度行
            progress1 = i
            progress2 = min(i * 0.8, 100)
            progress3 = min(i * 0.6, 100)
            
            table.add_row(
                "機器人 20 - 第 1 次",
                f"{create_progress_bar(progress1)} {progress1}%"
            )
            table.add_row(
                "機器人 20 - 第 2 次",
                f"{create_progress_bar(progress2)} {progress2:.0f}%"
            )
            table.add_row(
                "機器人 25 - 第 1 次",
                f"{create_progress_bar(progress3)} {progress3:.0f}%"
            )
            
            live.update(Panel(table, title=f"測試進度 (更新 #{i})"))
            time.sleep(0.1)
    
    console.print("✅ 進度演示完成\n")


def create_progress_bar(percentage: float, width: int = 20) -> str:
    """創建進度條"""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    color = "green" if percentage == 100 else "yellow"
    return f"[{color}]{bar}[/]"


if __name__ == "__main__":
    console = Console()
    
    # 顯示功能說明
    console.print("\n🚀 [bold cyan]RMFS 容量測試監控功能演示[/bold cyan]\n")
    console.print("新功能特性:")
    console.print("1. ▶️  [bold]背景執行[/bold] - 測試在背景運行，不阻塞選單")
    console.print("2. 📊 [bold]實時監控[/bold] - 查看測試進度和輸出")
    console.print("3. 🔄 [bold]多會話支援[/bold] - 同時運行多個測試會話")
    console.print("4. 📝 [bold]詳細輸出[/bold] - 查看每個測試的完整日誌\n")
    
    # 運行演示
    demo_monitor_ui()
    
    # 詢問是否演示動畫
    console.print("\n要查看進度動畫演示嗎？")
    response = input("輸入 y 查看動畫演示，其他鍵跳過: ")
    
    if response.lower() == 'y':
        demo_progress_animation()
    
    console.print("演示結束！使用 [bold]python test/experiment_menu.py[/bold] 體驗完整功能。\n")