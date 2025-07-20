#!/usr/bin/env python3
"""
DQN Training Visualizer
專門用於視覺化 DQN 訓練過程的工具
"""

import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
from datetime import datetime
import argparse
import warnings
warnings.filterwarnings('ignore')

# 設置樣式
sns.set_style("whitegrid")
plt.style.use('default')

class DQNTrainingVisualizer:
    def __init__(self, training_dir):
        """
        初始化 DQN 訓練視覺化器
        
        Args:
            training_dir: 訓練數據目錄路徑
        """
        self.training_dir = Path(training_dir)
        self.output_dir = self.training_dir / "visualizations"
        self.output_dir.mkdir(exist_ok=True)
        
        # 載入訓練歷史
        self.history_file = self.training_dir / "training_history.json"
        self.metadata_file = self.training_dir / "metadata.json"
        
        self.training_data = None
        self.metadata = None
        
    def load_data(self):
        """載入訓練數據"""
        if not self.history_file.exists():
            print(f"❌ 找不到訓練歷史文件: {self.history_file}")
            return False
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
            print(f"✅ 成功載入訓練歷史")
            
            # 載入 metadata（如果存在）
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"✅ 成功載入 metadata")
                
            return True
        except Exception as e:
            print(f"❌ 載入數據時發生錯誤: {e}")
            return False
    
    def plot_training_curves(self):
        """繪製訓練曲線"""
        if not self.training_data:
            return
            
        checkpoints = self.training_data.get('checkpoints', [])
        if not checkpoints:
            print("❌ 沒有找到檢查點數據")
            return
            
        # 提取數據
        ticks = [cp['tick'] for cp in checkpoints]
        rewards = [cp['episode_reward'] for cp in checkpoints]
        losses = [cp['avg_loss'] for cp in checkpoints]
        q_values = [cp['avg_q_value'] for cp in checkpoints]
        epsilons = [cp['epsilon'] for cp in checkpoints]
        completion_rates = [cp['completion_rate'] * 100 for cp in checkpoints]
        
        # 創建子圖
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('DQN Training Progress', fontsize=16, fontweight='bold')
        
        # 1. 累積獎勵
        ax = axes[0, 0]
        ax.plot(ticks, rewards, 'b-', linewidth=2)
        ax.set_title('Cumulative Episode Reward')
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Cumulative Reward')
        ax.grid(True, alpha=0.3)
        
        # 2. 平均損失
        ax = axes[0, 1]
        if any(loss > 0 for loss in losses):
            ax.plot(ticks, losses, 'r-', linewidth=2)
            ax.set_title('Average Loss')
            ax.set_xlabel('Training Steps')
            ax.set_ylabel('Loss')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.3)
        
        # 3. 平均 Q 值
        ax = axes[0, 2]
        ax.plot(ticks, q_values, 'g-', linewidth=2)
        ax.set_title('Average Q-Value')
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Q-Value')
        ax.grid(True, alpha=0.3)
        
        # 4. Epsilon 衰減
        ax = axes[1, 0]
        ax.plot(ticks, epsilons, 'm-', linewidth=2)
        ax.set_title('Epsilon Decay')
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Epsilon')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
        
        # 5. 訂單完成率
        ax = axes[1, 1]
        ax.plot(ticks, completion_rates, 'c-', linewidth=2)
        ax.set_title('Order Completion Rate')
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Completion Rate (%)')
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        
        # 6. 記憶體大小
        ax = axes[1, 2]
        memory_sizes = [cp['memory_size'] for cp in checkpoints]
        ax.plot(ticks, memory_sizes, 'orange', linewidth=2)
        ax.set_title('Replay Memory Size')
        ax.set_xlabel('Training Steps')
        ax.set_ylabel('Memory Size')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_path = self.output_dir / 'dqn_training_curves.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 訓練曲線已保存至: {save_path}")
    
    def plot_episode_analysis(self):
        """分析 episode 數據"""
        if not self.training_data:
            return
            
        episodes = self.training_data.get('episodes', [])
        if not episodes:
            print("❌ 沒有找到 episode 數據")
            return
            
        # 提取數據
        episode_nums = list(range(1, len(episodes) + 1))
        total_rewards = [ep['total_reward'] for ep in episodes]
        steps = [ep['steps'] for ep in episodes]
        avg_losses = [ep['avg_loss'] for ep in episodes]
        avg_q_values = [ep['avg_q_value'] for ep in episodes]
        
        # 創建圖表
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Episode-wise Analysis', fontsize=16, fontweight='bold')
        
        # 1. Episode 獎勵
        ax = axes[0, 0]
        ax.plot(episode_nums, total_rewards, 'b-', linewidth=2)
        # 添加移動平均線
        if len(total_rewards) > 10:
            ma = pd.Series(total_rewards).rolling(window=10).mean()
            ax.plot(episode_nums, ma, 'r--', linewidth=2, label='10-Episode MA')
        ax.set_title('Episode Total Reward')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Total Reward')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Episode 步數
        ax = axes[0, 1]
        ax.plot(episode_nums, steps, 'g-', linewidth=2)
        ax.set_title('Episode Length')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Steps')
        ax.grid(True, alpha=0.3)
        
        # 3. Episode 平均損失
        ax = axes[1, 0]
        valid_losses = [loss for loss in avg_losses if loss > 0]
        valid_episodes = [i for i, loss in enumerate(avg_losses, 1) if loss > 0]
        if valid_losses:
            ax.plot(valid_episodes, valid_losses, 'r-', linewidth=2)
            ax.set_title('Episode Average Loss')
            ax.set_xlabel('Episode')
            ax.set_ylabel('Average Loss')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.3)
        
        # 4. Episode 平均 Q 值
        ax = axes[1, 1]
        ax.plot(episode_nums, avg_q_values, 'm-', linewidth=2)
        ax.set_title('Episode Average Q-Value')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Average Q-Value')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_path = self.output_dir / 'dqn_episode_analysis.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Episode 分析已保存至: {save_path}")
    
    def plot_action_distribution(self):
        """繪製動作分布"""
        if not self.training_data:
            return
            
        episodes = self.training_data.get('episodes', [])
        if not episodes:
            return
            
        # 收集所有動作分布
        all_actions = []
        for ep in episodes:
            action_dist = ep.get('action_distribution', {})
            for action, count in action_dist.items():
                all_actions.extend([int(action)] * count)
        
        if not all_actions:
            print("❌ 沒有找到動作數據")
            return
            
        # 創建圖表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Action Distribution Analysis', fontsize=16, fontweight='bold')
        
        # 1. 整體動作分布
        action_counts = pd.Series(all_actions).value_counts().sort_index()
        action_labels = ['Keep', 'Switch to H', 'Switch to V']
        
        ax1.bar(action_counts.index, action_counts.values, color=['green', 'blue', 'red'])
        ax1.set_xticks(action_counts.index)
        ax1.set_xticklabels(action_labels)
        ax1.set_title('Overall Action Distribution')
        ax1.set_xlabel('Action')
        ax1.set_ylabel('Count')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. 動作分布隨時間變化
        episode_actions = []
        for i, ep in enumerate(episodes):
            action_dist = ep.get('action_distribution', {})
            total = sum(action_dist.values())
            if total > 0:
                percentages = [action_dist.get(str(a), 0) / total * 100 for a in range(3)]
                episode_actions.append(percentages)
        
        if episode_actions:
            episode_actions = np.array(episode_actions).T
            episodes_nums = list(range(1, len(episodes) + 1))
            
            for i, (action_data, label, color) in enumerate(zip(episode_actions, action_labels, ['green', 'blue', 'red'])):
                ax2.plot(episodes_nums, action_data, label=label, color=color, linewidth=2)
            
            ax2.set_title('Action Distribution Over Episodes')
            ax2.set_xlabel('Episode')
            ax2.set_ylabel('Action Percentage (%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 100)
        
        plt.tight_layout()
        save_path = self.output_dir / 'dqn_action_distribution.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 動作分布已保存至: {save_path}")
    
    def generate_summary_report(self):
        """生成訓練總結報告"""
        if not self.training_data:
            return
            
        report_path = self.output_dir / 'training_summary.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== DQN Training Summary Report ===\n\n")
            
            # Metadata 信息
            if self.metadata:
                f.write("Training Configuration:\n")
                f.write(f"  Controller Type: {self.metadata.get('controller_type', 'DQN')}\n")
                f.write(f"  Reward Mode: {self.metadata.get('reward_mode', 'N/A')}\n")
                f.write(f"  Start Time: {self.metadata.get('start_time', 'N/A')}\n")
                f.write(f"  End Time: {self.metadata.get('end_time', 'N/A')}\n")
                
                config = self.metadata.get('config', {})
                f.write(f"  Training Ticks: {config.get('training_ticks', 'N/A')}\n")
                f.write(f"  Batch Size: {config.get('batch_size', 'N/A')}\n")
                f.write(f"  Learning Rate: {config.get('learning_rate', 'N/A')}\n")
                f.write(f"  Gamma: {config.get('gamma', 'N/A')}\n")
                f.write(f"  Variant: {config.get('variant', 'default')}\n")
                f.write("\n")
            
            # 訓練統計
            checkpoints = self.training_data.get('checkpoints', [])
            episodes = self.training_data.get('episodes', [])
            
            if checkpoints:
                f.write("Training Statistics:\n")
                f.write(f"  Total Checkpoints: {len(checkpoints)}\n")
                f.write(f"  Total Episodes: {len(episodes)}\n")
                
                # 最終指標
                last_cp = checkpoints[-1]
                f.write(f"\nFinal Metrics:\n")
                f.write(f"  Final Epsilon: {last_cp['epsilon']:.4f}\n")
                f.write(f"  Final Memory Size: {last_cp['memory_size']}\n")
                f.write(f"  Final Episode Reward: {last_cp['episode_reward']:.2f}\n")
                f.write(f"  Final Completion Rate: {last_cp['completion_rate']:.2%}\n")
                
                # 平均指標
                all_rewards = [cp['episode_reward'] for cp in checkpoints]
                all_losses = [cp['avg_loss'] for cp in checkpoints if cp['avg_loss'] > 0]
                all_q_values = [cp['avg_q_value'] for cp in checkpoints]
                
                f.write(f"\nAverage Metrics:\n")
                f.write(f"  Average Episode Reward: {np.mean(all_rewards):.2f} ± {np.std(all_rewards):.2f}\n")
                if all_losses:
                    f.write(f"  Average Loss: {np.mean(all_losses):.6f} ± {np.std(all_losses):.6f}\n")
                f.write(f"  Average Q-Value: {np.mean(all_q_values):.2f} ± {np.std(all_q_values):.2f}\n")
                
                # 改善指標
                if len(all_rewards) > 10:
                    early_rewards = all_rewards[:10]
                    late_rewards = all_rewards[-10:]
                    improvement = (np.mean(late_rewards) - np.mean(early_rewards)) / abs(np.mean(early_rewards)) * 100
                    f.write(f"\nImprovement Metrics:\n")
                    f.write(f"  Reward Improvement: {improvement:.1f}%\n")
                    f.write(f"  Early Average Reward: {np.mean(early_rewards):.2f}\n")
                    f.write(f"  Late Average Reward: {np.mean(late_rewards):.2f}\n")
            
            # 最終結果
            if self.metadata and 'results' in self.metadata:
                results = self.metadata['results']
                f.write(f"\nFinal Results:\n")
                f.write(f"  Total Ticks: {results.get('total_ticks', 'N/A')}\n")
                f.write(f"  Completed Orders: {results.get('completed_orders', 'N/A')}\n")
                f.write(f"  Final Epsilon: {results.get('final_epsilon', 'N/A')}\n")
                f.write(f"  Cumulative Step Reward: {results.get('cumulative_step_reward', 'N/A')}\n")
        
        print(f"✅ 訓練總結報告已保存至: {report_path}")
    
    def visualize_all(self):
        """執行所有視覺化"""
        print("\n開始生成 DQN 訓練視覺化...")
        
        if not self.load_data():
            return
            
        self.plot_training_curves()
        self.plot_episode_analysis()
        self.plot_action_distribution()
        self.generate_summary_report()
        
        print(f"\n✅ 所有視覺化已完成！結果保存在: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description="DQN Training Visualizer")
    parser.add_argument('training_dir', type=str, help='Path to training directory')
    args = parser.parse_args()
    
    visualizer = DQNTrainingVisualizer(args.training_dir)
    visualizer.visualize_all()


if __name__ == "__main__":
    main()