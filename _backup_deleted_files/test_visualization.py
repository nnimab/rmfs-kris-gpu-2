#!/usr/bin/env python3
"""
Windows Testing Script for RMFS Visualization
Replaces training_manager.sh functionality for Windows users
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class WindowsTestManager:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.results_dir = self.project_dir / "models" / "training_runs"
        self.analysis_dir = self.project_dir / "analysis_results"
        
        print("🖥️  RMFS Windows Test Manager")
        print("="*50)
        print(f"📁 Project Directory: {self.project_dir}")
        print(f"📁 Results Directory: {self.results_dir}")
        print(f"📁 Analysis Directory: {self.analysis_dir}")
        print()
    
    def check_dependencies(self):
        """Check if required Python packages are installed"""
        required_packages = [
            'matplotlib', 'pandas', 'seaborn', 'numpy'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Installing missing packages...")
            
            for package in missing_packages:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    print(f"✅ Installed {package}")
                except subprocess.CalledProcessError:
                    print(f"❌ Failed to install {package}")
                    return False
        
        return True
    
    def check_training_results(self):
        """Check what training results are available"""
        print("\n🔍 Checking for training results...")
        
        if not self.results_dir.exists():
            print(f"❌ Results directory not found: {self.results_dir}")
            return []
        
        training_runs = []
        for run_dir in self.results_dir.iterdir():
            if run_dir.is_dir():
                metadata_file = run_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        controller_type = metadata.get('controller_type', 'unknown')
                        reward_mode = metadata.get('reward_mode', 'unknown')
                        
                        training_runs.append({
                            'name': run_dir.name,
                            'type': controller_type,
                            'mode': reward_mode,
                            'path': run_dir
                        })
                        
                        print(f"✅ Found: {controller_type}_{reward_mode} ({run_dir.name})")
                        
                    except Exception as e:
                        print(f"⚠️  Error reading {run_dir.name}: {e}")
        
        if not training_runs:
            print("❌ No valid training results found")
            print("💡 You can still test with simulated data using --test flag")
        
        return training_runs
    
    def run_visualization_test(self, use_test_data=False):
        """Run visualization with test data"""
        print(f"\n📊 Running visualization {'with test data' if use_test_data else 'with real data'}...")
        
        try:
            cmd = [sys.executable, 'visualization_generator_v2.py']
            if use_test_data:
                cmd.append('--test')
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Visualization completed successfully!")
                print("\nOutput:")
                print(result.stdout)
                
                # List generated files
                if self.analysis_dir.exists():
                    print(f"\n📁 Generated files in {self.analysis_dir}:")
                    for file in self.analysis_dir.iterdir():
                        if file.is_file():
                            print(f"  📄 {file.name}")
                
                return True
            else:
                print("❌ Visualization failed!")
                print("Error output:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error running visualization: {e}")
            return False
    
    def run_evaluation_test(self):
        """Test the evaluation script"""
        print("\n🎯 Testing evaluation script...")
        
        try:
            # Run a quick evaluation test
            cmd = [sys.executable, 'evaluate.py', '--eval_ticks', '100', '--num_runs', '1']
            
            print("⚠️  This is just a syntax check. Full evaluation requires trained models.")
            print("Command that would be run:", ' '.join(cmd))
            
            # Just check if the script can be imported
            result = subprocess.run([sys.executable, '-c', 'import evaluate; print("✅ Evaluation script syntax OK")'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print("❌ Evaluation script has syntax errors:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error testing evaluation: {e}")
            return False
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            print("\n" + "="*50)
            print("🖥️  RMFS Windows Test Manager")
            print("="*50)
            print()
            print("📊 Visualization Options:")
            print("  [1] Test visualization with simulated data")
            print("  [2] Run visualization with real training data")
            print("  [3] Check training results")
            print()
            print("🧪 Testing Options:")
            print("  [4] Test evaluation script syntax")
            print("  [5] Check Python dependencies")
            print()
            print("📁 File Operations:")
            print("  [6] Open analysis results folder")
            print("  [7] Clean analysis results")
            print()
            print("❌ Exit:")
            print("  [0] Exit")
            print()
            
            choice = input("Select option [0-7]: ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                self.run_visualization_test(use_test_data=True)
            elif choice == '2':
                training_runs = self.check_training_results()
                if training_runs:
                    self.run_visualization_test(use_test_data=False)
                else:
                    print("❌ No training data found. Try option 1 for test data.")
            elif choice == '3':
                self.check_training_results()
            elif choice == '4':
                self.run_evaluation_test()
            elif choice == '5':
                self.check_dependencies()
            elif choice == '6':
                self.open_results_folder()
            elif choice == '7':
                self.clean_results()
            else:
                print("❌ Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")
    
    def open_results_folder(self):
        """Open analysis results folder in Windows Explorer"""
        try:
            if self.analysis_dir.exists():
                os.startfile(str(self.analysis_dir))
                print(f"📁 Opened {self.analysis_dir} in Explorer")
            else:
                print(f"❌ Directory not found: {self.analysis_dir}")
                print("💡 Run visualization first to create results")
        except Exception as e:
            print(f"❌ Error opening folder: {e}")
    
    def clean_results(self):
        """Clean analysis results directory"""
        try:
            if self.analysis_dir.exists():
                import shutil
                
                files = list(self.analysis_dir.iterdir())
                if files:
                    confirm = input(f"⚠️  Delete {len(files)} files in {self.analysis_dir}? [y/N]: ")
                    if confirm.lower() == 'y':
                        shutil.rmtree(self.analysis_dir)
                        self.analysis_dir.mkdir()
                        print("✅ Analysis results cleaned")
                    else:
                        print("❌ Cancelled")
                else:
                    print("📁 Directory is already empty")
            else:
                print("📁 Analysis directory doesn't exist")
        except Exception as e:
            print(f"❌ Error cleaning results: {e}")

def main():
    """Main function"""
    print("🖥️  Starting RMFS Windows Test Manager...")
    
    # Check if we're on Windows
    if os.name != 'nt':
        print("⚠️  This script is designed for Windows. On Linux/Mac, use training_manager.sh")
    
    manager = WindowsTestManager()
    
    # Check dependencies first
    if not manager.check_dependencies():
        print("❌ Dependency check failed. Please install required packages manually.")
        return
    
    # Show interactive menu
    manager.show_menu()

if __name__ == "__main__":
    main()