# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Git Ignore Configuration:** Added comprehensive `.gitignore` file to manage version control exclusions:
  - Excludes Python cache files, virtual environments, and compiled files
  - Ignores machine learning model files (*.pth, *.pkl, *.h5)
  - Excludes CSV files with numeric suffixes while preserving template files (e.g., keeps `generated_backlog.csv` but ignores `generated_backlog_61004.csv`)
  - Completely excludes `result/` directory and `models/training_runs/` directory
  - Preserves backup files and input data while excluding large files and temporary analysis results
- **V5.0 Reward System:** Implemented comprehensive V5.0 reward system with spillback penalty mechanism:
  - Extended observation vector from 16 to 17 dimensions to include picking station queue length
  - Added spillback penalty accumulator in UnifiedRewardSystem for global mode
  - Integrated picking station queue monitoring in warehouse tick()
- **Enhanced Energy Model:** Improved robot energy consumption calculation with realistic physics:
  - Added startup energy cost (0.5 units) when robots transition from idle to moving
  - Implemented regenerative braking with 30% energy recovery efficiency
  - Distinguished between acceleration (with inertia cost) and deceleration energy consumption

### Changed
- **NERL Performance Optimization:** Implemented batch processing in the `evaluate_individual_parallel` function (`train.py`) to significantly speed up NERL training. The loop now collects all required intersection states, processes them in a single batch on the GPU, and sets all actions at once. This drastically reduces Python-NetLogo I/O overhead and improves GPU utilization.
- **Unified Network Architecture & Hyperparameters:** To ensure a fair and stable comparison for the thesis experiments, the following major changes were implemented:
  - **Unified Network:** Both `DQN` and `NERL` now use an identical, modern network architecture (`1024 -> 512 (BatchNorm) -> 256 -> action_size`), replacing the previous asymmetrical and oversized models. This ensures comparability.
  - **DQN Hyperparameters:** The `memory_size` in `DeepQNetwork` has been increased to `100,000` and the `batch_size` is now configurable, defaulting to `512` to better utilize modern GPU capabilities.
  - **Global Reward `time_cost`:** The weight for time penalty was corrected to `-0.001` to avoid excessive punishment in early training stages.

### Fixed
- **DQN Training Crash:** Fixed a `TypeError` in `dqn_controller.py` where the `replay` method was called with an unexpected `batch_size` keyword argument. The `DeepQNetwork.replay` method sources the batch size from its own configuration, so the redundant argument was removed from the call site.
- **AttributeError in Progress Reward:** Fixed a crash (`AttributeError: 'Order' object has no attribute 'assigned_robot_id'`) in the `progress_reward` calculation. The issue was resolved by:
  1. Adding a `robot_id` attribute to the `Order` class.
  2. Updating the `Warehouse.tick` method to assign the `robot.id` to the `order.robot_id` when a job is assigned.
  3. Correcting the logic in `unified_reward_system.py` to use the new `order.robot_id` attribute.
- **Reward System Tuning:** Overhauled the global reward function to provide denser rewards in early training.
  - **Introduced Progress Reward:** Added a new `progress_reward` to the global fitness calculation. Agents now receive positive rewards for achieving intermediate goals, such as moving a robot to a target pod (`+10`) or successfully picking up the pod (`+25`). This addresses the sparse reward problem by guiding the agent towards completing orders.
  - **Adjusted Time Penalty:** The `time_cost` weight was adjusted from `-0.01` to `-0.001` to reduce the heavy penalty in early training stages, based on diagnostic data showing no orders were being completed.
- **Reward System Overhaul:** Completely redesigned the reward calculation logic in `ai/unified_reward_system.py` to prevent reward hacking and numerical instability.
  - **Global Mode:** The reward is now correctly calculated based on "Energy Efficiency" (completed orders / total energy), directly reflecting the core research KPI. Only truly completed customer orders (positive ID, `order_complete_time` set) are counted, eliminating loopholes from internal tasks like replenishment.
  - **Step Mode:** The reward is now a pure, clipped cost function (`[-1.0, 1.0]`), providing stable, negative gradients for learning. The unreliable `passing_reward` has been removed.
- **Parallel Training File Collision:** Resolved a critical race condition that occurred when running with multiple workers (`--parallel_workers > 1`).
  - Implemented a PID-based file generation system in `lib/generator/warehouse_generator.py` to ensure each worker process operates on its own unique data files.
  - Added a robust `try...finally` block in `train.py` and a `cleanup_temp_files` function in `netlogo.py` to ensure temporary data files are reliably deleted after each process, preventing disk clutter and errors in subsequent runs. 