# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **NERL Evolution Analysis:** Extended `analysis/paper_analyzer.py` to support analysis of NERL training logs.
  - Added `analyze_nerl_evolution` function to parse fitness scores from each generation's `fitness_scores.json`.
  - The script now generates evolution curve plots showing max, mean, and min fitness per generation, providing insights into convergence and population diversity.
  - The main function was updated with a new `nerl-evolution` analysis type.

### Changed
- **Thesis Content:** In `thesis/第三章/3.2.1_倉儲模擬環境設計.md`, added a new section "4. 交叉路口設計與分類" to define and classify "Standard Intersections" and "Critical Intersections". This section explains their strategic importance as bottlenecks and provides the rationale for their special handling in the reward function, and includes a suggestion for a new diagram.
- **Switched to JSON-based Log Parsing:** Refactored `analysis/paper_analyzer.py` to parse structured JSON summaries instead of raw text logs for DQN analysis. This approach proved more robust against malformed log files and encoding issues. The script now attempts to find and parse JSON objects embedded in log lines.
- **Skipped DQN Analysis:** Decided to omit the detailed DQN training performance analysis (`4.2.1`) from the thesis to focus on the core NERL methodology. The corresponding TODO task was cancelled.

### Fixed
- **Analysis Script Title Bug:** Fixed an issue in `analysis/paper_analyzer.py` where generated plots were overwriting each other due to a static default title. The script now uses the experiment directory name as the default title, ensuring unique filenames for each analysis run.

### In Progress
- **Chapter 4 Writing:**
  - Completed the initial draft of `thesis/第四章/4.2.2_NERL演化過程分析.md`.
  - The section includes a detailed analysis of a baseline NERL experiment and comparative analysis across different configurations (Exploration vs. Exploitation, Step vs. Global Reward, Short vs. Long Evaluation).
  - All generated evolution plots have been embedded in the document.

## [2025-07-24]

### Added
- **Advanced NERL Analysis Modes:** Significantly upgraded `analysis/paper_analyzer.py` based on user feedback for deeper insights.
  - **Elite KPI Evolution Analysis (`nerl-elite-kpi`)**: Added a new mode to track and plot the evolution of key performance indicators (e.g., `completion_rate`, `energy_per_order`) for the *elite individual* of each generation. This provides a clear view of multi-objective optimization over time.
  - **Final Model Comparison (`nerl-final-comparison`)**: Implemented a second new mode to generate comparative bar charts of the final performance of all NERL experimental groups. This allows for direct comparison of the "champion" models produced by each training configuration.
  - **Enhanced Plotting**: All new plots use English labels, and the comparison charts feature a sophisticated color and pattern-coding scheme to clearly distinguish between different experimental parameters (reward mode, variant, evaluation ticks).
- **Full Suite of Analysis Plots:** Generated a complete set of new visualizations for the thesis.
  - One elite KPI evolution plot for each of the 8 NERL experiment groups.
  - Six final model comparison bar charts, one for each key performance indicator.

### Changed
- **Complete Overhaul of Thesis Section 4.2.2:** Rewrote `thesis/第四章/4.2.2_NERL演化過程與最終效能分析.md` from scratch to incorporate the new, more insightful analysis. The new section is structured around the two new analysis modes: elite evolution and final model comparison, providing a much stronger narrative for the results.

### Fixed
- **Analysis Script Robustness:** Greatly improved the fault tolerance of `analysis/paper_analyzer.py`. The script can now gracefully handle missing or corrupted `fitness_scores.json` files in any generation, skipping the problematic file and logging a warning instead of crashing. This was crucial for successfully analyzing the `B_nerl_step_b3000ticks` experiment.

## [2025-07-23]

### Added
- **English Translation of Chapter 3:** Created a complete English version of "Chapter 3: Methodology" (`thesis/Chapter_3_Methodology.md`). The translation adheres to the project's academic writing standards, including correct mathematical notation, and maintains structural consistency with other chapters.
- **English Translation of Chapter 1:** Created an English version of "Chapter 1: Introduction" (`thesis/Chapter_1_Introduction.md`) to facilitate international review and dissemination. The translation adheres to academic standards and follows the project's writing guidelines.
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
- **Thesis Formatting:** Added sequential equation numbers (e.g., `(3-1)`) to all mathematical formulas in `thesis/Chapter_3_Methodology.md` to adhere to academic standards.
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