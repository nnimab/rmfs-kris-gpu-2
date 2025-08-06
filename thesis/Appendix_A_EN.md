# Appendix A: Detailed Experimental Data

This appendix provides the detailed raw data used in the final performance verification in Chapter 4, for reference and to ensure the reproducibility of the study. All experimental groups were run independently four times. In the `time_based` group, one run produced anomalous data, so only three runs were considered in the final analysis.

| Short Name | Experiment Group | Run 1 | Run 2 | Run 3 | Run 4 |
|:---|:---|---:|---:|---:|---:|
| `Baseline-T` | time_based | 0.8372 | 0.8651 | 1.0000 | 0.8744 |
| `Baseline-Q` | queue_based | 0.8774 | 0.8868 | 0.8632 | 0.8930 |
| `Baseline-N` | no_controller | 0.9116 | 0.8698 | 0.8930 | 0.8791 |
| `DQN-S` | dqn_dqn_model_step_55000 | 0.8868 | 0.8930 | 0.8679 | 0.8868 |
| `DQN-G` | dqn_dqn_model_global_55000 | 0.8645 | 0.8774 | 0.8791 | 0.8726 |
| `NERL-S-A3` | nerl_nerl_step_a3000ticks | 0.8632 | 0.8037 | 0.8698 | 0.8884 |
| `NERL-G-A3` | nerl_nerl_global_a3000ticks | 0.8779 | 0.8372 | 0.8915 | 0.8774 |
| `NERL-S-B3` | nerl_nerl_step_b3000ticks | 0.8140 | 0.8791 | 0.8651 | 0.8679 |
| `NERL-G-B3` | nerl_nerl_global_b3000ticks | 0.8915 | 0.8726 | 0.8545 | 0.8744 |
| `NERL-S-A8` | nerl_nerl_step_a8000ticks | 0.8605 | 0.8879 | 0.7840 | 0.8977 |
| `NERL-G-A8` | nerl_nerl_global_a8000ticks | 0.8113 | 0.8679 | 0.8826 | 0.8093 |
| `NERL-S-B8` | nerl_nerl_step_b8000ticks | 0.8632 | 0.8538 | 0.8585 | 0.8349 |
| `NERL-G-B8` | nerl_nerl_global_b8000ticks | 0.8113 | 0.8785 | 0.8698 | 0.8585 |

Table: Table A.1: Completion Rate by Experiment Group

| Short Name | Experiment Group | Run 1 | Run 2 | Run 3 | Run 4 |
|:---|:---|---:|---:|---:|---:|
| `Baseline-T` | time_based | 178.39 | 162.15 | 96.89 | 148.35 |
| `Baseline-Q` | queue_based | 188.27 | 216.31 | 222.40 | 147.63 |
| `Baseline-N` | no_controller | 164.07 | 191.30 | 188.76 | 176.29 |
| `DQN-S` | dqn_dqn_model_step_55000 | 190.30 | 168.76 | 182.59 | 191.14 |
| `DQN-G` | dqn_dqn_model_global_55000 | 204.53 | 179.96 | 158.39 | 195.47 |
| `NERL-S-A3` | nerl_nerl_step_a3000ticks | 94.30 | 107.34 | 159.87 | 129.60 |
| `NERL-G-A3` | nerl_nerl_global_a3000ticks | 205.75 | 133.39 | 156.92 | 180.84 |
| `NERL-S-B3` | nerl_nerl_step_b3000ticks | 83.73 | 182.30 | 132.00 | 193.67 |
| `NERL-G-B3` | nerl_nerl_global_b3000ticks | 166.78 | 158.51 | 145.55 | 155.93 |
| `NERL-S-A8` | nerl_nerl_step_a8000ticks | 136.85 | 178.05 | 101.71 | 144.65 |
| `NERL-G-A8` | nerl_nerl_global_a8000ticks | 107.65 | 124.06 | 165.75 | 73.71 |
| `NERL-S-B8` | nerl_nerl_step_b8000ticks | 153.12 | 119.66 | 165.35 | 138.59 |
| `NERL-G-B8` | nerl_nerl_global_b8000ticks | 131.54 | 136.17 | 182.85 | 147.61 |

Table: Table A.2: Average Energy per Order (EU) by Experiment Group

| Short Name | Experiment Group | Run 1 | Run 2 | Run 3 | Run 4 |
|:---|:---|---:|---:|---:|---:|
| `Baseline-T` | time_based | 32109.78 | 30159.90 | 2519.17 | 27889.10 |
| `Baseline-Q` | queue_based | 35018.22 | 40665.94 | 40699.73 | 28345.27 |
| `Baseline-N` | no_controller | 32157.26 | 35773.67 | 36242.39 | 33318.04 |
| `DQN-S` | dqn_dqn_model_step_55000 | 35776.77 | 32401.14 | 33597.36 | 35933.80 |
| `DQN-G` | dqn_dqn_model_global_55000 | 37838.09 | 33473.07 | 29935.20 | 36161.23 |
| `NERL-S-A3` | nerl_nerl_step_a3000ticks | 17257.56 | 18463.16 | 29894.77 | 24753.72 |
| `NERL-G-A3` | nerl_nerl_global_a3000ticks | 38474.63 | 24009.76 | 29657.39 | 33635.35 |
| `NERL-S-B3` | nerl_nerl_step_b3000ticks | 14652.40 | 34454.22 | 24552.61 | 35634.48 |
| `NERL-G-B3` | nerl_nerl_global_b3000ticks | 31522.25 | 29325.01 | 26490.08 | 29315.15 |
| `NERL-S-A8` | nerl_nerl_step_a8000ticks | 25317.03 | 33828.57 | 16984.92 | 27917.54 |
| `NERL-G-A8` | nerl_nerl_global_a8000ticks | 18516.25 | 22826.60 | 31160.86 | 12824.91 |
| `NERL-S-B8` | nerl_nerl_step_b8000ticks | 28021.24 | 21658.44 | 30093.40 | 24531.09 |
| `NERL-G-B8` | nerl_nerl_global_b8000ticks | 22625.20 | 25599.53 | 34192.48 | 26865.70 |

Table: Table A.3: Total Energy Consumption (EU) by Experiment Group

| Short Name | Experiment Group | Run 1 | Run 2 | Run 3 | Run 4 |
|:---|:---|---:|---:|---:|---:|
| `Baseline-T` | time_based | 180 | 186 | 26 | 188 |
| `Baseline-Q` | queue_based | 186 | 188 | 183 | 192 |
| `Baseline-N` | no_controller | 196 | 187 | 192 | 189 |
| `DQN-S` | dqn_dqn_model_step_55000 | 188 | 192 | 184 | 188 |
| `DQN-G` | dqn_dqn_model_global_55000 | 185 | 186 | 189 | 185 |
| `NERL-S-A3` | nerl_nerl_step_a3000ticks | 183 | 172 | 187 | 191 |
| `NERL-G-A3` | nerl_nerl_global_a3000ticks | 187 | 180 | 189 | 186 |
| `NERL-S-B3` | nerl_nerl_step_b3000ticks | 175 | 189 | 186 | 184 |
| `NERL-G-B3` | nerl_nerl_global_b3000ticks | 189 | 185 | 182 | 188 |
| `NERL-S-A8` | nerl_nerl_step_a8000ticks | 185 | 190 | 167 | 193 |
| `NERL-G-A8` | nerl_nerl_global_a8000ticks | 172 | 184 | 188 | 174 |
| `NERL-S-B8` | nerl_nerl_step_b8000ticks | 183 | 181 | 182 | 177 |
| `NERL-G-B8` | nerl_nerl_global_b8000ticks | 172 | 188 | 187 | 182 |

Table: Table A.4: Completed Orders by Experiment Group

| Short Name | Experiment Group | Run 1 | Run 2 | Run 3 | Run 4 |
|:---|:---|---:|---:|---:|---:|
| `Baseline-T` | time_based | 9900 | 9900 | 594 | 9900 |
| `Baseline-Q` | queue_based | 12367 | 13232 | 12760 | 13168 |
| `Baseline-N` | no_controller | 0 | 0 | 0 | 0 |
| `DQN-S` | dqn_dqn_model_step_55000 | 13266 | 13212 | 13312 | 12975 |
| `DQN-G` | dqn_dqn_model_global_55000 | 13386 | 13416 | 13986 | 13123 |
| `NERL-S-A3` | nerl_nerl_step_a3000ticks | 12748 | 10663 | 12643 | 12315 |
| `NERL-G-A3` | nerl_nerl_global_a3000ticks | 11898 | 12656 | 12199 | 12133 |
| `NERL-S-B3` | nerl_nerl_step_b3000ticks | 12108 | 12212 | 12755 | 11847 |
| `NERL-G-B3` | nerl_nerl_global_b3000ticks | 12366 | 11748 | 11730 | 12153 |
| `NERL-S-A8` | nerl_nerl_step_a8000ticks | 12121 | 12522 | 11860 | 12252 |
| `NERL-G-A8` | nerl_nerl_global_a8000ticks | 11590 | 11883 | 12435 | 12170 |
| `NERL-S-B8` | nerl_nerl_step_b8000ticks | 12027 | 12534 | 11977 | 11452 |
| `NERL-G-B8` | nerl_nerl_global_b8000ticks | 11907 | 11628 | 12193 | 11884 |

Table: Table A.5: Total Signal Switches by Experiment Group 