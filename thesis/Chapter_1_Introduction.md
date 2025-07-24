# Chapter 1: Introduction

## 1.1 Research Background and Motivation

The global retail industry is undergoing a structural transformation driven by e-commerce. Projections indicate that the annual value of global retail e-commerce will grow to \$6.42 trillion by 2025, accounting for over 20% of total retail sales [1]. To cope with the new normal of e-commerce orders—characterized by "small batches, high frequency, and time sensitivity"—traditional warehousing models are no longer adequate. This has prompted businesses to adopt **Robotic Mobile Fulfillment Systems (RMFS)** on a large scale. In an RMFS, hundreds of Autonomous Mobile Robots (AMRs) work collaboratively within a grid-based warehouse, capable of increasing order picking efficiency by several folds.

However, the high-density operation of AMRs also introduces new operational bottlenecks. **Traffic congestion at intersections, waiting delays between robots, and frequent acceleration and deceleration behaviors** not only directly limit the overall throughput of the system but also significantly increase energy consumption and carbon emissions. This issue has become critically important under the increasingly stringent global policies on sustainable development and carbon neutrality:

*   **High Carbon Footprint**: Carbon emissions from transportation and warehousing activities account for approximately 24% of total global greenhouse gas emissions and have been identified as a priority area for carbon reduction by international logistics leaders like DHL [2].
*   **Urgent Policy Pressure**: The European Union's **Carbon Border Adjustment Mechanism (CBAM)** was initiated in 2023 and is scheduled to be fully implemented in 2026. This mechanism will impose additional costs on imported products with high carbon intensity, compelling companies throughout the supply chain to rigorously inspect and manage carbon emissions in their warehousing and transportation links [3].

Against this backdrop, academia has begun to apply intelligent methods such as Reinforcement Learning (RL) to optimize RMFS operations. Some studies have used deep reinforcement learning to schedule orders to minimize costs [4], while others have reduced total energy consumption by about 3–5% by adjusting traffic strategies and robot speeds [5]. However, these studies either focus on order-level scheduling or still have room for exploration in the trade-off between energy consumption and efficiency. **Currently, a control framework that focuses on the intersection level and aims for the dual optimization of "energy-efficiency" is still lacking.**

To fill this research gap, this study proposes an intersection controller based on **Neuroevolution Reinforcement Learning (NERL)**. This method combines the global search capabilities of evolutionary algorithms with the real-time decision-making advantages of deep reinforcement learning. It aims to provide an "adaptive, energy-aware" right-of-way allocation mechanism for RMFS intersections, with the expectation of effectively reducing the energy consumption per task for AMRs while maintaining order processing efficiency.

## 1.2 Research Objectives

To validate the aforementioned concept and address the core research questions, this study formulates the following four specific objectives. The results will be elaborated in subsequent chapters:

1.  **Construct a High-Fidelity RMFS Simulation and Control Platform**
    *   Establish a physical warehouse environment that includes a central storage area, one-way aisles, workstations, and charging stations.
    *   Design a modular traffic control system architecture based on the Strategy and Factory design patterns to support the flexible integration and fair comparison of different algorithms (see Section 3.2 for details).

2.  **Design and Implement Multiple Traffic Control Strategies**
    *   Develop two heuristic baseline controllers: a **Time-Based Controller** based on fixed time cycles, and a **Queue-Based Controller** based on real-time waiting queues (see Section 3.3 for details).
    *   Implement a value-based deep reinforcement learning method, the **Deep Q-Network (DQN)**, to serve as a benchmark for DRL comparison (see Section 3.4.1 for details).
    *   Develop the core contribution of this research, the **Neuroevolution Reinforcement Learning (NERL) Controller**, and investigate the impact of different evolutionary hyperparameters (exploratory vs. exploitative) (see Section 3.4.2 for details).

3.  **Design and Execute Rigorous Controlled Experiments**
    *   Define a comprehensive set of performance evaluation metrics covering efficiency, throughput, and stability (see Section 3.2.4 for details).
    *   Design a comparative matrix with twelve independent experimental groups to systematically compare the performance of different controllers under two reward modes (step-based reward vs. global reward) and different evaluation durations (see Section 3.6.1 for details).

4.  **Quantitative Analysis and Statistical Validation**
    *   Conduct an in-depth quantitative analysis and comparison of the performance of all control strategies based on experimental data.
    *   Employ statistical methods, such as the independent samples t-test, to scientifically verify whether the performance improvement of the proposed NERL method is statistically significant compared to the baseline controllers (see Section 3.5.4 for details).

## 1.3 Research Scope and Limitations

To focus on the core problem and ensure the depth of the research, this study explicitly defines its scope. The following sections list the core areas covered by this research and the aspects excluded to simplify the model.

### 1.3.1 Scope of Research

| Item                 | Content                                                              | Description                                                                                                       |
| :------------------- | :------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------- |
| **Core Problem**     | Dynamic allocation of right-of-way at intersections.                 | The research focuses on resolving congestion and energy waste caused by improper traffic coordination at intersections. |
| **Control Strategies** | Time-Based, Queue-Based, DQN, NERL.                                  | Encompasses a comprehensive comparison from static rules and dynamic heuristics to two different DRL frameworks. |
| **Optimization Goals** | Minimize total energy consumption, maximize order completion, minimize average waiting time. | Adopts a multi-objective optimization perspective to evaluate the overall performance of strategies in terms of efficiency and energy consumption. |
| **Evaluation Metrics** | Efficiency, throughput, and stability metrics defined in Section 3.2.4. | Utilizes a complete set of quantitative metrics to thoroughly evaluate the pros and cons of each controller.        |

### 1.3.2 Research Limitations

This study intentionally excludes the following issues from its scope to maintain focus on the core problem. These issues can serve as directions for future research.

*   **Path Planning**: This research does not involve global path planning algorithms for robots from start to destination. It is assumed that all robots follow a predefined shortest path.
*   **Slotting Assignment**: This research does not optimize the storage location of stock-keeping units (SKUs) on shelves or the placement of shelves within the warehouse. It is assumed that these are randomly or pre-configured.
*   **Charging Strategy Management**: Although charging stations exist in the simulation environment, this study does not involve monitoring robot battery levels and proactively dispatching them for charging. 