#!/usr/bin/env python3
"""
Simplified RMFS Controller Evaluation for Windows Testing
Focuses on data validation and basic comparison
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse

class SimpleEvaluator:
    def __init__(self, results_dir="models/training_runs", output_dir="evaluation_results"):
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set English labels
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
    def load_training_results(self):
        """Load and validate training results"""
        results = {}
        
        if not self.results_dir.exists():
            print(f"⚠️  Results directory not found: {self.results_dir}")
            return self.create_demo_results()
        
        print(f"🔍 Loading results from {self.results_dir}")
        
        for run_dir in self.results_dir.iterdir():
            if not run_dir.is_dir():
                continue
                
            metadata_file = run_dir / "metadata.json"
            if not metadata_file.exists():
                continue
                
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                controller_type = metadata.get('controller_type', 'unknown')
                reward_mode = metadata.get('reward_mode', 'unknown')
                
                # Extract final performance
                final_results = metadata.get('results', {})
                
                if controller_type == 'nerl':
                    # Get from final evaluation
                    completed_orders = final_results.get('completed_orders_final_eval', 0)
                    total_energy = final_results.get('total_energy_final_eval', 0)
                    best_fitness = final_results.get('best_fitness', 0)
                    
                    # Try to get more details from last generation
                    last_gen_file = None
                    gen_dirs = sorted([d for d in run_dir.glob("gen*") if d.is_dir()])
                    if gen_dirs:
                        last_gen_file = gen_dirs[-1] / "fitness_scores.json"
                    
                    if last_gen_file and last_gen_file.exists():
                        with open(last_gen_file, 'r') as f:
                            last_gen = json.load(f)
                        
                        metrics = last_gen.get('best_individual_metrics', {})
                        completion_rate = metrics.get('completion_rate', 0)
                        avg_wait_time = metrics.get('avg_wait_time', 0)
                        energy_per_order = metrics.get('energy_per_order', 0)
                        robot_utilization = metrics.get('robot_utilization', 0)
                    else:
                        completion_rate = completed_orders / 50 if completed_orders > 0 else 0
                        avg_wait_time = 0
                        energy_per_order = total_energy / completed_orders if completed_orders > 0 else 0
                        robot_utilization = 0
                        
                elif controller_type == 'dqn':
                    completed_orders = final_results.get('completed_orders', 0)
                    total_energy = 0
                    best_fitness = final_results.get('cumulative_step_reward', 0)
                    completion_rate = completed_orders / 50 if completed_orders > 0 else 0
                    avg_wait_time = 0
                    energy_per_order = 0
                    robot_utilization = 0
                
                else:
                    continue
                
                # Validate data
                completed_orders = max(0, min(50, completed_orders or 0))
                completion_rate = max(0, min(1, completion_rate or 0))
                avg_wait_time = max(0, avg_wait_time or 0)
                energy_per_order = max(0, energy_per_order or 0)
                robot_utilization = max(0, min(1, robot_utilization or 0))
                
                results[f"{controller_type}_{reward_mode}"] = {
                    'controller_type': controller_type,
                    'reward_mode': reward_mode,
                    'completed_orders': completed_orders,
                    'completion_rate': completion_rate * 100,  # Convert to percentage
                    'avg_wait_time': avg_wait_time,
                    'energy_per_order': energy_per_order,
                    'robot_utilization': robot_utilization * 100,  # Convert to percentage
                    'best_fitness': best_fitness,
                    'total_energy': total_energy,
                    'run_name': run_dir.name
                }
                
                print(f"✅ Loaded {controller_type}_{reward_mode}: {completed_orders} orders, {completion_rate*100:.1f}% rate")
                
            except Exception as e:
                print(f"⚠️  Error loading {run_dir.name}: {e}")
        
        if not results:
            print("❌ No valid results found, creating demo data")
            return self.create_demo_results()
        
        return results
    
    def create_demo_results(self):
        """Create demo results for testing"""
        print("🧪 Creating demo results for testing...")
        
        return {
            'nerl_global': {
                'controller_type': 'nerl',
                'reward_mode': 'global',
                'completed_orders': 14,
                'completion_rate': 28.0,
                'avg_wait_time': 25.3,
                'energy_per_order': 165.4,
                'robot_utilization': 85.2,
                'best_fitness': 1.29,
                'total_energy': 2315.6,
                'run_name': 'demo_nerl_global'
            },
            'nerl_step': {
                'controller_type': 'nerl',
                'reward_mode': 'step',
                'completed_orders': 8,
                'completion_rate': 16.0,
                'avg_wait_time': 31.2,
                'energy_per_order': 203.1,
                'robot_utilization': 78.5,
                'best_fitness': -45.2,
                'total_energy': 1624.8,
                'run_name': 'demo_nerl_step'
            },
            'dqn_global': {
                'controller_type': 'dqn',
                'reward_mode': 'global',
                'completed_orders': 10,
                'completion_rate': 20.0,
                'avg_wait_time': 28.7,
                'energy_per_order': 0,
                'robot_utilization': 82.1,
                'best_fitness': 0.85,
                'total_energy': 0,
                'run_name': 'demo_dqn_global'
            },
            'dqn_step': {
                'controller_type': 'dqn',
                'reward_mode': 'step',
                'completed_orders': 7,
                'completion_rate': 14.0,
                'avg_wait_time': 33.1,
                'energy_per_order': 0,
                'robot_utilization': 75.3,
                'best_fitness': -125.4,
                'total_energy': 0,
                'run_name': 'demo_dqn_step'
            },
            'queue_based': {
                'controller_type': 'traditional',
                'reward_mode': 'queue',
                'completed_orders': 12,
                'completion_rate': 24.0,
                'avg_wait_time': 29.8,
                'energy_per_order': 0,
                'robot_utilization': 80.4,
                'best_fitness': 0,
                'total_energy': 0,
                'run_name': 'demo_queue_based'
            },
            'time_based': {
                'controller_type': 'traditional',
                'reward_mode': 'time',
                'completed_orders': 9,
                'completion_rate': 18.0,
                'avg_wait_time': 26.5,
                'energy_per_order': 0,
                'robot_utilization': 77.2,
                'best_fitness': 0,
                'total_energy': 0,
                'run_name': 'demo_time_based'
            }
        }
    
    def create_comparison_charts(self, results):
        """Create comparison charts"""
        df = pd.DataFrame.from_dict(results, orient='index')
        
        # Define colors for different controller types
        colors = {
            'nerl': '#2E8B57',
            'dqn': '#4169E1', 
            'traditional': '#FF6B6B'
        }
        
        charts_created = []
        
        # 1. Completion Rate Comparison
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(range(len(df)), df['completion_rate'],
                     color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        
        ax.set_title('Order Completion Rate Comparison', fontsize=14, fontweight='bold')
        ax.set_ylabel('Completion Rate (%)')
        ax.set_xlabel('Controller')
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df.index, rotation=45, ha='right')
        
        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        filename = f"completion_rate_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        charts_created.append(filepath)
        print(f"✅ Created: {filename}")
        
        # 2. Wait Time Comparison (only if we have data)
        if df['avg_wait_time'].sum() > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            bars = ax.bar(range(len(df)), df['avg_wait_time'],
                         color=[colors.get(ct, '#808080') for ct in df['controller_type']])
            
            ax.set_title('Average Wait Time Comparison', fontsize=14, fontweight='bold')
            ax.set_ylabel('Average Wait Time (ticks)')
            ax.set_xlabel('Controller')
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df.index, rotation=45, ha='right')
            
            # Add value labels
            for i, bar in enumerate(bars):
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            filename = f"wait_time_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            charts_created.append(filepath)
            print(f"✅ Created: {filename}")
        
        # 3. Robot Utilization Comparison
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(range(len(df)), df['robot_utilization'],
                     color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        
        ax.set_title('Robot Utilization Comparison', fontsize=14, fontweight='bold')
        ax.set_ylabel('Robot Utilization (%)')
        ax.set_xlabel('Controller')
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df.index, rotation=45, ha='right')
        
        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        filename = f"robot_utilization_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        charts_created.append(filepath)
        print(f"✅ Created: {filename}")
        
        # 4. Overall Performance Summary
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Controller Performance Summary', fontsize=16, fontweight='bold')
        
        # Completion Rate
        bars1 = ax1.bar(range(len(df)), df['completion_rate'],
                       color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        ax1.set_title('Completion Rate (%)')
        ax1.set_xticks(range(len(df)))
        ax1.set_xticklabels(df.index, rotation=45, ha='right')
        
        # Completed Orders
        bars2 = ax2.bar(range(len(df)), df['completed_orders'],
                       color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        ax2.set_title('Completed Orders')
        ax2.set_xticks(range(len(df)))
        ax2.set_xticklabels(df.index, rotation=45, ha='right')
        
        # Wait Time (if available)
        if df['avg_wait_time'].sum() > 0:
            bars3 = ax3.bar(range(len(df)), df['avg_wait_time'],
                           color=[colors.get(ct, '#808080') for ct in df['controller_type']])
            ax3.set_title('Avg Wait Time (ticks)')
        else:
            ax3.text(0.5, 0.5, 'No Wait Time Data', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Avg Wait Time (ticks)')
        ax3.set_xticks(range(len(df)))
        ax3.set_xticklabels(df.index, rotation=45, ha='right')
        
        # Robot Utilization
        bars4 = ax4.bar(range(len(df)), df['robot_utilization'],
                       color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        ax4.set_title('Robot Utilization (%)')
        ax4.set_xticks(range(len(df)))
        ax4.set_xticklabels(df.index, rotation=45, ha='right')
        
        plt.tight_layout()
        filename = f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        charts_created.append(filepath)
        print(f"✅ Created: {filename}")
        
        return charts_created, df
    
    def generate_report(self, results, df):
        """Generate evaluation report"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_file = self.output_dir / f"evaluation_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RMFS Controller Performance Evaluation Report\n")
            f.write("="*60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Controllers Evaluated: {len(results)}\n\n")
            
            # Performance ranking
            sorted_df = df.sort_values('completion_rate', ascending=False)
            
            f.write("1. Performance Ranking (by Completion Rate)\n")
            f.write("-"*40 + "\n")
            for i, (name, row) in enumerate(sorted_df.iterrows(), 1):
                f.write(f"{i}. {name}:\n")
                f.write(f"   Completion Rate: {row['completion_rate']:.1f}%\n")
                f.write(f"   Completed Orders: {row['completed_orders']}\n")
                f.write(f"   Robot Utilization: {row['robot_utilization']:.1f}%\n")
                if row['avg_wait_time'] > 0:
                    f.write(f"   Avg Wait Time: {row['avg_wait_time']:.1f} ticks\n")
                f.write(f"   Best Fitness: {row['best_fitness']:.3f}\n\n")
            
            # Summary statistics
            f.write("2. Summary Statistics\n")
            f.write("-"*40 + "\n")
            f.write(f"Best Completion Rate: {df['completion_rate'].max():.1f}% ({df['completion_rate'].idxmax()})\n")
            f.write(f"Average Completion Rate: {df['completion_rate'].mean():.1f}%\n")
            f.write(f"Best Robot Utilization: {df['robot_utilization'].max():.1f}% ({df['robot_utilization'].idxmax()})\n")
            
            if df['avg_wait_time'].sum() > 0:
                min_wait_idx = df[df['avg_wait_time'] > 0]['avg_wait_time'].idxmin()
                f.write(f"Lowest Wait Time: {df.loc[min_wait_idx, 'avg_wait_time']:.1f} ticks ({min_wait_idx})\n")
            
            # Controller type analysis
            f.write("\n3. Controller Type Analysis\n")
            f.write("-"*40 + "\n")
            
            for controller_type in df['controller_type'].unique():
                subset = df[df['controller_type'] == controller_type]
                f.write(f"\n{controller_type.upper()} Controllers:\n")
                f.write(f"  Count: {len(subset)}\n")
                f.write(f"  Avg Completion Rate: {subset['completion_rate'].mean():.1f}%\n")
                f.write(f"  Best Performance: {subset['completion_rate'].max():.1f}% ({subset['completion_rate'].idxmax()})\n")
            
            # Recommendations
            f.write("\n4. Recommendations\n")
            f.write("-"*40 + "\n")
            best_controller = sorted_df.index[0]
            f.write(f"• Best Overall Performance: {best_controller}\n")
            f.write(f"• Achieved {sorted_df.iloc[0]['completion_rate']:.1f}% completion rate\n")
            
            if 'nerl_global' in df.index and 'nerl_step' in df.index:
                global_rate = df.loc['nerl_global', 'completion_rate']
                step_rate = df.loc['nerl_step', 'completion_rate']
                if global_rate > step_rate:
                    f.write("• NERL Global reward mode outperforms Step reward mode\n")
                else:
                    f.write("• NERL Step reward mode outperforms Global reward mode\n")
            
            f.write("• Consider hybrid approaches combining best features\n")
            f.write("• Focus on improving completion rates for practical deployment\n")
        
        print(f"✅ Report saved: {report_file}")
        return report_file
    
    def run_evaluation(self):
        """Run the complete evaluation"""
        print("🎯 Starting RMFS Controller Evaluation...")
        
        # Load results
        results = self.load_training_results()
        print(f"✅ Loaded {len(results)} controller results")
        
        # Create comparison charts
        print("\n📊 Creating comparison charts...")
        charts, df = self.create_comparison_charts(results)
        
        # Generate report
        print("\n📝 Generating evaluation report...")
        report = self.generate_report(results, df)
        
        # Save data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.output_dir / f"evaluation_data_{timestamp}.csv"
        df.to_csv(csv_file, index=True)
        print(f"✅ Data saved: {csv_file}")
        
        print("\n" + "="*50)
        print("🎯 Evaluation Complete!")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📊 Charts created: {len(charts)}")
        print(f"📝 Report: {report.name}")
        print(f"📄 Data: {csv_file.name}")
        print("="*50)
        
        return {
            'charts': charts,
            'report': report,
            'data': csv_file,
            'results': results
        }

def main():
    parser = argparse.ArgumentParser(description="Simple RMFS Controller Evaluation")
    parser.add_argument('--results_dir', default='models/training_runs',
                       help='Training results directory')
    parser.add_argument('--output_dir', default='evaluation_results',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    evaluator = SimpleEvaluator(args.results_dir, args.output_dir)
    results = evaluator.run_evaluation()
    
    return results

if __name__ == "__main__":
    main()