# Chapter 2: Literature Review

## 2.1 Chapter Overview

This chapter aims to systematically review the research related to traffic management in Robotic Mobile Fulfillment Systems (RMFS). The chapter will unfold progressively: first, it will elaborate on the root causes of traffic congestion in RMFS and its profound impact on system performance. Subsequently, it will sequentially evaluate three categories of control strategies relevant to this study—traditional heuristic methods, mainstream Deep Reinforcement Learning (DRL) approaches, and emerging Neuroevolution methods—assessing their applications, achievements, and limitations in addressing this problem. Through this structured analysis, the chapter aims to precisely identify the existing research gap and ultimately articulate the necessity and novelty of proposing a traffic control strategy that integrates energy considerations and is based on Neuroevolution Reinforcement Learning (NERL).

## 2.2 Robotic Mobile Fulfillment Systems: Operational Efficiency and Traffic Bottlenecks

As a "Goods-to-Person" paradigm in warehouse automation, the core of RMFS involves using a large number of Autonomous Mobile Robots (AMRs) to transport mobile shelves (Pods), thereby replacing traditional manual picking routes and significantly enhancing order fulfillment efficiency [6]. Since the acquisition and large-scale deployment of Kiva Systems by Amazon [7], RMFS has become a fundamental infrastructure for modern e-commerce logistics. Studies indicate that its throughput can be two to four times that of traditional warehouses. As companies like Amazon deploy over 750,000 robots, the operational density and complexity of these systems have reached unprecedented levels [8].

However, high-density deployment brings a new and severe bottleneck: **Traffic Congestion**. As defined in Chapter 3 of this study, when a large number of robots execute tasks within a limited network of aisles, especially at intersections, conflicts and waiting periods are highly likely to occur due to improper right-of-way coordination [9]. This triggers a series of cascading negative effects, not only causing delays in order fulfillment and reducing overall system throughput, but recent research also indicates that frequent stop-and-go behaviors significantly increase overall energy consumption [10] and may accelerate the aging of robot batteries, thereby increasing operational costs. Therefore, designing an **intersection management strategy** that is adaptive and balances both efficiency and energy sustainability has become a core challenge in enhancing the overall performance of RMFS.

Within the complex decision-making framework of RMFS, traffic control and path planning are the elements most directly related to the system's real-time performance. In recent years, many studies have focused on solving this problem. For example, **Luo et al. (2023) [11]** proposed a path planning method combining the A* algorithm and DQN, while **Zhou et al. (2024) [12]** used an attention-based DRL model to collaboratively handle multi-AGV scheduling and pod reconfiguration problems. These studies highlight the immense potential of intelligent algorithms in RMFS operational optimization. Although this research focuses on intersection traffic control, its optimization goal—enhancing system fluidity and efficiency—is fundamentally aligned with these studies.

## 2.3 Review and Analysis of Intersection Traffic Control Methods

To address the intersection traffic problem in RMFS, various control strategies have been proposed in academia and industry. Their development can be broadly categorized into heuristic methods and learning-based methods, reflecting an evolutionary trend from static rules to dynamic, adaptive control.

### 2.3.1 Heuristic and Rule-based Controllers

Early solutions often relied on manually designed heuristic rules. Their advantages include simplicity of implementation and low computational overhead, making them common baselines for evaluating the performance of more complex algorithms.

One category is **Static Time-based Control**, which borrows from traditional urban traffic light systems to set fixed right-of-way switching cycles for intersections. This concept aligns with early fixed-rule urban traffic solutions [13] and corresponds to the **`TimeBasedController`** designed in Section 3.3.1 of this study. However, its fundamental drawback is its complete inability to perceive real-time traffic flow changes. When traffic fluctuates dramatically, this static strategy is prone to wasting green light time on idle directions or causing unnecessary queue buildup in busy directions.

To address the shortcomings of static methods, another category, **Dynamic Reactive Control**, emerged. These methods react to the real-time state of an intersection, such as the length of waiting queues. For instance, the study by **Teja (2009) [14]** assigned agents to intersections to manage traffic flow based on the priority of incoming robots. This approach forms the conceptual basis for the **`QueueBasedController`** designed in Section 3.3.2 of this study. Although more flexible, the design of these heuristic rules heavily relies on expert experience and prior knowledge. Their predefined weights and logic struggle to capture the optimal coordination strategy in complex traffic patterns, often leading to suboptimal performance in highly dynamic and non-linear traffic scenarios [15].

### 2.3.2 Deep Reinforcement Learning (DRL) Based Controllers

To overcome the limitations of manual rules, Deep Reinforcement Learning (DRL) has been widely applied to traffic control problems. DRL enables an agent (the controller) to autonomously learn complex decision-making policies from interactions with the environment to maximize long-term cumulative rewards [16].

This paradigm has achieved significant success in the macroscopic field of **urban traffic signal control**. Numerous studies have demonstrated that methods based on Deep Q-Networks (DQN) and their variants significantly outperform traditional methods in reducing vehicle delays and increasing network throughput [17]. For example, **Cao et al. (2024) [18]** proposed G-DQN to improve convergence speed; **Zhu et al. (2021) [19]** compared the performance of PPO and DQN in single-intersection control; and **Angela et al. (2024) [20]** designed a reward function that incorporates multi-dimensional information such as pressure, queue length, and speed to train DQN agents. These studies fully showcase the powerful capabilities of DRL in handling sequential decision-making problems.

In recent years, researchers have begun to transfer this paradigm to RMFS scenarios. They typically use local traffic information at intersections (e.g., queue length, waiting time) as the **State**, switching traffic phases as the **Action**, and maximizing throughput or minimizing waiting time as the **Reward** to train the controller [21] [22]. Although DQN-based methods show great potential, they also face inherent challenges:
1.  **Reward Design Sensitivity**: The performance of DQN is highly dependent on dense and well-designed real-time reward signals. As analyzed in Section 3.4.3 of this study, poor or overly simplistic reward designs can lead the agent to learn unintended, suboptimal behaviors (e.g., frequently oscillating signals just to receive switching rewards).
2.  **Risk of Local Optima**: In complex, high-dimensional state spaces, gradient-based optimization methods can sometimes converge to local optima, making it difficult to discover globally optimal coordination strategies.
3.  **Sample Efficiency Issues**: DQN typically requires a large number of environmental interaction samples to learn an effective policy, and the training process can be very time-consuming.

Given the representativeness and maturity of DQN in this field, this study uses it as a key **baseline** for objectively evaluating the potential improvements offered by the proposed new method.

## 2.4 The Potential of Neuroevolution Reinforcement Learning (NERL)

To address the challenges faced by traditional DRL methods, this study introduces another optimization paradigm: Neuroevolution Reinforcement Learning (NERL). Unlike DQN, which attempts to learn a value function, NERL searches directly in the **parameter space** of the policy network. It treats the weights of a neural network as an individual's "genes" and uses evolutionary algorithms (such as elitism, crossover, and mutation) to optimize an entire population of agents, ultimately yielding high-performance control policies [23].

NERL exhibits several unique advantages in solving complex control problems, making it particularly suitable for the objectives of this research:
1.  **Robustness to Reward Functions**: Evolutionary algorithms are gradient-free, black-box optimization methods that do not require the reward function to be continuous or differentiable. This makes them naturally suited for handling **sparse, delayed, or globally-defined reward signals**. For example, the "total number of completed orders" or "total energy consumption" over an entire simulation period can be directly used as a fitness function. This aligns perfectly with the **Global Reward** concept designed in Section 3.4.3 of this study, thereby avoiding tedious reward engineering.
2.  **Stronger Global Exploration**: The crossover and mutation operations in the evolutionary process facilitate broader exploration of the parameter space. By maintaining population diversity, this reduces the risk of getting trapped in local optima and increases the likelihood of discovering innovative and efficient control strategies.
3.  **Inherent Parallelism**: The evaluation process for each individual (policy network) in the population is independent and can be deployed in a massively parallel fashion on multi-core CPUs or computing clusters. This allows for the efficient use of modern computational resources, significantly reducing the wall-clock time for training [24].

Although neuroevolution has achieved remarkable success in fields like robotics control and game AI [25], **its specific application to RMFS intersection traffic control, and its systematic comparison against traditional heuristic methods and mainstream DRL methods (like DQN) on a unified platform that considers both time efficiency and energy consumption, remains a largely unexplored area.**


## 2.5 Chapter Summary and Research Gap

Based on the analysis above, the development trajectory of existing RMFS traffic control research clearly points to several key unresolved issues. Control strategies are evolving from simple static rules to dynamic heuristics, and further to adaptive methods based on DRL. However, existing DRL methods (mainly DQN) still face challenges in reward design, avoidance of local optima, and optimization for long-term global objectives. Meanwhile, most traffic control research focuses on throughput and time delay, while studies that treat **energy consumption** as a core optimization objective of equal importance to efficiency are relatively scarce.

More importantly, the potential of neuroevolution—as a method with stronger global exploration capabilities and greater robustness to sparse, global rewards—has not been systematically explored or validated for the RMFS traffic control problem.

Therefore, the core **research gap** of this study can be summarized as: **the lack of an intelligent control strategy for RMFS that can effectively balance and optimize both traffic efficiency and energy consumption, while overcoming the limitations of traditional DRL in areas such as reward design and local optima.**

To fill this gap, this thesis proposes an intersection controller based on Neuroevolution Reinforcement Learning (NERL). We will conduct a comprehensive comparison of NERL with traditional heuristic methods and a standard DQN method on a high-fidelity simulation platform that incorporates a detailed energy consumption model. This research not only aims to propose a superior control strategy but also provides a solid empirical basis for evaluating the strengths and weaknesses of different learning paradigms in solving complex multi-agent coordination problems.

To more intuitively compare this study with related literature, Table 2.1 summarizes the similarities and differences between selected representative studies and this research in terms of problem definition, decision criteria, and algorithmic approaches.

**Table 2.1: Comparison with Related Research**

| Reference | Performance | Energy | Dynamic Routing | Traffic Strategy | Collision Handling | Multi-Agent | Analysis | Heuristic | Simulation | Reinforcement Learning |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Li et al. (2020) **[10]** | ✓ | ✓ | | | | ✓ | ✓ | | ✓ | |
| Luo et al. (2023) **[11]** | ✓ | | ✓ | | ✓ | | | ✓ | ✓ | ✓ |
| Yuan et al. (2023) **[26]** | ✓ | | | | ✓ | ✓ | | | ✓ | ✓ |
| Zhou et al. (2024) **[27]** | ✓ | | ✓ | ✓ | | ✓ | | | ✓ | ✓ |
| Cao et al. (2024) **[18]** | ✓ | | | ✓ | | | | | ✓ | ✓ |
| **This Study (Ours)** | **✓** | **✓** | ✓ | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | 