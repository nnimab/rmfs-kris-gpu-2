# Chapter 3: Methodology

## 3.1 Problem Definition

In modern automated warehouses utilizing Robotic Mobile Fulfillment Systems (RMFS), as order volumes grow and robot deployment density increases, traffic congestion has become the core bottleneck constraining overall operational efficiency. A large number of robots executing tasks within limited aisle space, especially at intersections, are prone to conflicts and waiting due to improper right-of-way coordination. This triggers a series of cascading negative effects, including: delayed order fulfillment times, energy waste from robots idling, and a decrease in the overall system throughput.

Therefore, the core problem of this research is: **How to design an effective and adaptive traffic control strategy to dynamically regulate right-of-way at intersections, thereby minimizing robot waiting times and overall energy consumption, and ultimately enhancing the operational efficiency of the entire warehouse system?**

To answer this question, it is first necessary to construct an experimental platform that can accurately simulate the aforementioned challenges. The experimental environment and system architecture described in this chapter constitute a high-fidelity testbed tailored for this core problem. Its purpose is to provide a stable, controllable, and quantifiable foundation for the implementation, training, and comparison of different control algorithms in the subsequent chapters.

## 3.1.1 Chapter Structure

This section aims to provide a comprehensive introduction to the experimental platform supporting this research. The content will cover four core parts: first, a detailed elaboration of the constructed warehouse simulation environment, including its physical layout and core entities (Section 3.2.1); second, a description of the traffic control system architecture designed for algorithm evaluation (Section 3.2.2); third, a list of the specific hardware and software configurations used in the experiments (Section 3.2.3); and finally, a definition of the quantitative evaluation metrics used to measure the effectiveness of various control strategies (Section 3.2.4). Through this section's explanation, readers will gain a complete understanding of the foundational environment and evaluation criteria for the experiments.

## 3.2 Experimental Environment and System Architecture

To effectively validate and compare the Neuroevolution Reinforcement Learning (NERL) traffic control strategy proposed in this study with other baseline methods, it is essential to construct a high-fidelity simulation platform that accurately reflects the challenges of real-world warehouse operations. This platform is not only a testing ground for algorithms but also a prerequisite for ensuring that all comparisons are conducted on a fair, controllable, and quantifiable basis.

This section will comprehensively describe the composition of this experimental platform. The content is divided into four core parts:
- **3.2.1 Warehouse Simulation Environment Design**: Details the physical layout, network structure of the simulated world, and the core entity components, including robots, pods, and workstations.
- **3.2.2 Traffic Control System Architecture**: Provides an in-depth analysis of the software architecture designed for algorithm integration and evaluation, explaining how the system drives decisions, executes control, and triggers learning.
- **3.2.3 Experimental Hardware and Software Configuration**: Lists the specific hardware specifications and software libraries used for all simulation and training experiments.
- **3.2.4 Performance Evaluation Metrics Definition**: Clearly defines the key quantitative indicators (KPIs) used to measure the effectiveness of different control strategies, serving as the basis for the experimental results analysis in later chapters.

Through this section, readers will gain a complete understanding of the foundational environment and evaluation criteria for the experiments conducted in this study.

## 3.2.1 Warehouse Simulation Environment Design

To effectively evaluate traffic control strategies, this study first constructed a high-fidelity warehouse simulation environment. This environment not only defines the physical layout but also includes various dynamic entities and their interaction rules, collectively forming a complex Robotic Mobile Fulfillment System (RMFS). This section details its design.

### 1. Physical Environment and Layout

The simulated warehouse is built on a two-dimensional discrete grid, where each grid cell has a specific function. The overall layout adopts a functional zoning design to ensure an orderly operational flow.

-   **Central Storage Area**: Located in the center of the warehouse, it consists of a dense arrangement of **Pod Locations**. The aisles in this area are designed as strict **One-way Aisles**, with the flow directions of horizontal and vertical aisles alternating. This design greatly simplifies the complexity of traffic management at a physical level, aiming to reduce potential conflicts when robots travel in opposite directions.
-   **Workstation Area**: Distributed on both sides of the warehouse. One side features **Picking Stations**, which are the exit points for order fulfillment, while the other side has **Replenishment Stations**, which are the entry points for goods into the system.
-   **Charging Station**: Scattered within the storage area, converted from some pod locations, for robots to charge autonomously.

**【圖表建議：圖 3.2.1 - 倉儲佈局示意圖】**
為直觀展示佈局，建議此處插入一張示意圖，用不同顏色標示出儲存區、揀貨區、補貨區與充電站，並用箭頭清晰標示出單向通道的流動方向。

### 2. Core Entities and Lifecycles

The dynamic behavior of the system is driven by the interactions between several core entities.

-   **Robot**: As the most central active unit in the system, the robot has a complex state machine to manage its workflow, including states like `idle`, `taking_pod`, `delivering_pod`, `station_processing`, and `returning_pod`. This study establishes a detailed physical and energy model for the robot. Its energy consumption calculation considers not only the load but also startup costs and regenerative braking (recovering energy from braking), providing a solid foundation for energy efficiency evaluation. Additionally, robots are equipped with priority-based autonomous collision avoidance logic, enabling them to resolve local conflicts to some extent.

**【圖表建議：圖 3.2.2 - 機器人狀態轉換圖】**
為清晰展示機器人的工作流程，建議此處插入一張 UML 狀態機圖，描繪其核心狀態以及觸發狀態轉換的事件（如「分配新任務」、「到達工作站」等）。

-   **Pod**: The mobile carrier for storing stock-keeping units (SKUs). Each pod can store multiple types of SKUs and records the current quantity and replenishment threshold for each SKU. When the stock level falls below the threshold, the system automatically triggers a corresponding replenishment task.

-   **Station**: The node for human-robot collaboration. After a robot delivers a pod to a workstation, the system simulates the delay of a worker picking or replenishing items. To handle high traffic, workstations are also designed with a dynamic path adjustment mechanism, activating a longer backup path to alleviate congestion when there are too many robots in the station.

### 3. Order and Task Flow

The simulation is driven by orders. An **Order** represents a customer's request, containing multiple SKUs to be picked. The system breaks down an order into one or more **Jobs**. The core of a job is "transporting a specified pod to a specified workstation," which is the smallest work unit that can be directly assigned to a robot. The entire process is as follows:
1.  The system receives an order.
2.  The SKUs required for the order are located on specific pods.
3.  The system generates one or more jobs and places them in the job queue.
4.  An idle robot takes a job from the queue and begins its lifecycle of picking up, delivering, and returning the pod.
5.  When all SKUs for an order have been successfully delivered to the workstation, the order is marked as complete.

## 3.2.2 Traffic Control System Architecture

To enable flexible integration and fair comparison of different traffic control algorithms, this study designed a modular software architecture based on the **Strategy Pattern** and the **Factory Pattern**. The core of this architecture is to separate the "decision-making algorithm" from the "system execution framework," ensuring that whether it's a simple rule-based logic or a complex deep reinforcement learning model, it can operate and be evaluated on the same foundation. The system primarily consists of the following three components:

### 1. `TrafficController` (Abstract Base Class for Traffic Controllers)
This Abstract Base Class (ABC) defines a unified interface that all traffic control strategies must adhere to. Its most critical method is `get_direction(intersection, tick, warehouse)`, which receives the current detailed state of the intersection (local information) and the state of the entire warehouse system (global information), and returns a traffic decision for that intersection (e.g., `"Horizontal"` or `"Vertical"`). By forcing all controllers to implement this interface, the system ensures consistency in how different algorithms are called. Additionally, the base class integrates standardized data collection functionalities for recording various performance metrics.

### 2. `TrafficControllerFactory` (Controller Factory)
This class employs the Factory design pattern and is responsible for dynamically creating instances of `TrafficController` subclasses based on external settings (such as the controller type specified in the experiment configuration file). When the simulation core needs a controller, it only needs to provide a string identifier like `"dqn"`, `"nerl"`, or `"time_based"`, and the factory will return a corresponding, initialized controller object. This design completely decouples the "creation logic" from the "usage logic" of the controllers, greatly enhancing the flexibility and scalability of the experimental workflow and allowing for switching between different control strategies without modifying any core simulation code.

### 3. `IntersectionManager` (Intersection Manager)
The Intersection Manager is the central coordinator and execution engine of the entire traffic control system. Its operational flow constitutes a complete closed-loop control system:
1.  **Holds a Controller Instance**: During the simulation initialization phase, the `IntersectionManager` obtains the controller instance required for the current experiment through the controller factory.
2.  **Drives the Decision Loop**: At each time unit (tick) of the simulation, the manager iterates through all intersections in the warehouse.
3.  **Gets a Decision**: For each intersection, it calls the `get_direction()` method of the `TrafficController` instance to obtain the traffic command for that intersection.
4.  **Executes the Decision**: Based on the command returned by the controller, the `IntersectionManager` updates the internal state of the intersection, such as changing the allowed direction of passage.
5.  **Triggers Model Training**: Specifically for reinforcement learning-based controllers (DQN/NERL), after the decision and execution steps are completed, the `IntersectionManager` will then call their `train()` method, providing the state transition that just occurred (State-Action-Reward-NextState) to the model, enabling it to learn and optimize from experience.

**【圖表建議：圖 3.2.1 - 交通控制系統運作序列圖】**

為使讀者能更直觀地理解此運作流程，強烈建議在此處插入一張 **UML 序列圖 (Sequence Diagram)**。該圖應清晰地展示從模擬器主迴圈 (`Simulation Loop`) 觸發，到 `IntersectionManager` 遍歷路口，再到 `TrafficController` 進行決策 (`get_direction`)，最後由 `IntersectionManager` 更新路口狀態 (`updateAllowedDirection`) 並觸發學習 (`train`) 的完整訊息傳遞順序。 

## 3.2.3 Experimental Hardware and Software Configuration

To ensure the reproducibility and validity of the results of this study, all simulation, training, and evaluation experiments were conducted on a clearly defined hardware platform and within a standardized software environment. This section will detail the relevant configurations.

### Hardware Configuration

The computational tasks of this study were primarily divided into two parts: model training on a high-performance cloud platform, and development, debugging, and results analysis on a local machine.

#### Training Environment (Runpod Secure Cloud)
All computationally intensive model training tasks were performed on the Runpod cloud platform to leverage its powerful computational resources and accelerate the learning process.
- **CPU**: 42 vCPUs
- **GPU**: 1 x NVIDIA GeForce RTX 4090
- **Memory (RAM)**: 83 GB

#### Development and Analysis Environment (Laptop)
Program development, initial testing, parameter tuning, and final data analysis and visualization were completed on a local computer.
- **CPU**: AMD Ryzen 9 6900HX
- **GPU**: NVIDIA GeForce RTX 3080 Ti
- **Memory (RAM)**: 16.0 GB

### Software Configuration

The choice of software environment aimed to balance development efficiency, computational performance, and broad community support.
- **Operating System**:
    - **Training Environment**: Ubuntu 22.04 (in a `runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel` Docker container)
    - **Development Environment**: Microsoft Windows 11
- **Programming Language**: `Python 3.10`
- **Core Computational Libraries**:
    - `PyTorch` (version `2.1.0`): Served as the core deep learning framework for building and training DQN and NERL neural network models.
    - `numpy` (version `1.24.4`): Provided the foundation for all numerical computations, widely used in state representation, reward calculation, etc.
    - `pandas` (version `2.0.3`): Primarily used for processing, storing, and analyzing experimental data.
- **Simulation and Analysis Tools**:
    - `networkx` (version `3.2.1`): Used for constructing and analyzing the warehouse's network graph structure.
    - `scikit-learn` (version `1.5.2`): Mainly used in this study for preprocessing steps like data normalization.
- **Visualization Libraries**:
    - `matplotlib` (version `3.7.2`): Used for generating static 2D plots such as line graphs and bar charts.
    - `seaborn` (version `0.13.2`): Based on matplotlib, provided more aesthetically pleasing and statistically-oriented visualizations like heatmaps.
- **System Tools**:
    - `psutil` (version `5.9.8`): Used for monitoring system resource usage.

**【表格建議：表 3.2.2 - 軟體函式庫與用途】**

為使軟體配置更加一目了然，建議在此處插入一個表格。該表格應包含三欄：「函式庫」、「版本號」與「在研究中的主要用途」，將上述所有函式庫整理進去。 

## 3.2.4 Performance Evaluation Metrics Definition

To objectively and quantitatively evaluate the pros and cons of different traffic control strategies, this study established a comprehensive set of Key Performance Indicators (KPIs). To define them clearly, we first agree on the following mathematical notations:
- \\( R \\): The set of all robots in the warehouse.
- \\( O_{completed} \\): The set of all completed orders during the simulation period.
- \\( P \\): The set of all passing events of robots through intersections.
- \\( T_{sim} \\): The total simulation duration (ticks).

### 1. Efficiency Metrics

**Total Energy Consumption**
This metric measures the overall energy efficiency of the system and is one of the core optimization targets of this study. It is calculated as the sum of the energy consumed by all robot activities during the simulation.
\\[
E_{total} = \sum_{r \in R} E_r
\\]
where \\( E_r \\) represents the total energy consumption of a single robot \\( r \\) throughout the simulation.

**Average Robot Utilization**
This metric reflects the overall business level of the robot fleet. It is defined as the average percentage of time that all robots are in a non-idle state relative to the total simulation time.
\\[
U_{avg} = \frac{1}{|R|} \sum_{r \in R} \frac{t_{active}(r)}{T_{sim}}
\\]
where \\( |R| \\) is the total number of robots, and \\( t_{active}(r) \\) is the total active time of robot \\( r \\).

### 2. Throughput Metrics

**Completed Orders Count**
This metric directly measures the total output of the system within a fixed time, reflecting its overall operational efficiency.
\\[
N_{orders} = |O_{completed}|
\\]

**Average Order Processing Time**
This metric measures the system's response speed for a single order. It is defined as the average time taken for all completed orders from the start of processing to the end.
\\[
T_{avg\_order} = \frac{1}{|O_{completed}|} \sum_{o \in O_{completed}} (t_{complete}(o) - t_{start}(o))
\\]
where \\( t_{complete}(o) \\) and \\( t_{start}(o) \\) are the completion and start times of order \\( o \\), respectively.

**Average Intersection Waiting Time**
This metric directly reflects the coordination efficiency of the traffic control strategy. It calculates the average waiting time for each event of a robot passing through an intersection.
\\[
W_{avg} = \frac{1}{|P|} \sum_{p \in P} t_{wait}(p)
\\]
where \\( |P| \\) is the total number of times robots pass through intersections, and \\( t_{wait}(p) \\) is the waiting time for a single passing event \\( p \\).

### 3. Stability Metrics

**Total Stop-and-Go Count**
This metric reflects the smoothness of the traffic flow. Frequent stop-and-go events not only consume extra energy but also indicate unstable traffic flow.
\\[
S_{total} = \sum_{r \in R} N_{s-g}(r)
\\]
where \\( N_{s-g}(r) \\) is the total number of times robot \\( r \\) stops and starts at intersections due to waiting.

## 3.3 Baseline Controller Design

To objectively and rigorously evaluate the performance of the deep reinforcement learning traffic control methods proposed in this study (see Section 3.4), they must be compared against a set of representative and easily understandable baseline controllers. Baseline controllers provide a performance reference point, enabling us to quantify the actual improvements brought by complex algorithms. An ideal baseline should reflect current industry practices or intuitive solutions.

This study employs two different but representative logics to design the baseline controllers: one is a fixed-time controller that completely ignores real-time traffic conditions, and the other is a dynamic controller that reacts to the immediate demands at intersections. These two represent the fundamental forms of static and dynamic control strategies, respectively, and can comprehensively measure the adaptability and superiority of reinforcement learning models in various traffic scenarios.

This section will sequentially detail the internal design principles, decision logic, and key parameters of the following two baseline controllers:

1.  **Time-Based Controller**: A static controller that switches right-of-way based on a fixed time cycle.
2.  **Queue-Based Controller**: A dynamic reactive controller that makes decisions based on the length of waiting queues at intersections and task priorities.

## 3.3.1 Time-Based Controller

The `TimeBasedController` is the most fundamental static traffic control strategy. Its core idea is derived from traditional urban traffic signal systems, completely ignoring real-time traffic flow or any dynamic changes at the intersection. It relies solely on a pre-set, fixed time cycle to alternate the right-of-way between horizontal and vertical directions. The advantage of this method lies in its extreme simplicity and predictability, but its disadvantage is equally obvious—it cannot adapt to fluctuations in traffic demand, easily causing unnecessary waiting during busy periods or wasting passage time during sparse traffic.

### Design Principle and Decision Logic

The operation of this controller is determined entirely by three parameters: the green light time for the horizontal direction ($T_{H\_green}$), the green light time for the vertical direction ($T_{V\_green}$), and the total signal cycle length ($T_{cycle}$), which is the sum of the two.

$$
T_{cycle} = T_{H\_green} + T_{V\_green}
$$

At any given time tick in the simulation, the controller determines the current position in the signal cycle ($t_{pos}$) using a modulo operation:

$$
t_{pos} = \text{tick} \bmod T_{cycle}
$$

Based on the value of $t_{pos}$, the controller makes a decision on the direction of passage. If $t_{pos}$ is less than the horizontal green time $T_{H\_green}$, it grants the right-of-way to the horizontal direction; otherwise, it grants it to the vertical direction. The decision rule can be expressed as:

$$
\text{Direction} = 
\begin{cases} 
\text{Horizontal,} & \text{if } t_{pos} < T_{H\_green} \\
\text{Vertical,} & \text{if } t_{pos} \geq T_{H\_green}
\end{cases}
$$

In our warehouse environment, since pods are primarily arranged along the horizontal direction, the frequency and volume of robot movement are much higher horizontally than vertically. To accommodate this characteristic, we have set a longer green time for the horizontal direction (e.g., $T_{H\_green} = 70$ ticks) and a relatively shorter green time for the vertical direction (e.g., $T_{V\_green} = 30$ ticks) in our parameter settings, aiming to achieve a preliminary traffic balance without considering real-time status.

**[Figure Suggestion: Figure 3.3.1 - Time-Based Controller Signal Cycle Diagram]**

It is recommended to insert a timeline diagram here to clearly illustrate the composition of $T_{cycle}$, marking the intervals for $T_{H\_green}$ and $T_{V\_green}$, and the corresponding traffic direction decisions (Horizontal/Vertical) in different intervals.

## 3.3.2 Queue-Based Controller

The `QueueBasedController` is a dynamic reactive control strategy designed to address the fundamental flaw of the `TimeBasedController`, which is its inability to perceive real-time traffic demands. This controller continuously monitors the waiting queues in both directions of an intersection and dynamically calculates the right-of-way based on the urgency of the tasks being performed by the robots. Compared to the static `TimeBasedController`, the `QueueBasedController` can adapt more flexibly to changes in traffic flow, prioritizing the allocation of passage resources to the direction with more urgent demand.

### Design Principle and Decision Logic

The core of this controller is to quantify and combine two key factors for decision-making: **the number of robots** and **task priority**.

#### 1. Task Priority Weighting System

In warehouse operations, not all robot tasks have the same level of importance. For example, a robot delivering a pod to a picking station, if delayed, will directly impact order fulfillment efficiency. In contrast, an empty robot heading to the storage area has a relatively lower task urgency. To reflect this difference, we have defined a set of priority weights ($W_{priority}$) for different robot states (`robot.current_state`):

| Robot State (`current_state`) | Task Description | Priority Weight ($W_{priority}$) |
| :--- | :--- | :---: |
| `delivering_pod` | Delivering a pod to a picking station | 3.0 |
| `returning_pod` | Returning a pod to the storage area | 2.0 |
| `taking_pod` | Going to the storage area to pick up a pod | 1.0 |
| `idle` | Idle or on standby | 0.5 |
| `station_processing` | Processing within a picking station | 0.0 |

#### 2. Directional Priority Calculation

For each direction of the intersection (horizontal H or vertical V), the controller calculates a weighted priority sum ($P_{H}$ or $P_{V}$). This value is the sum of the task priority weights of all waiting robots ($R_{dir}$) in that direction. The formula is as follows:

$$
P_{dir} = \sum_{i \in R_{dir}} W_{priority}(i)
$$

where $W_{priority}(i)$ represents the priority weight corresponding to the current state of robot $i$.

Additionally, considering the inherent higher traffic flow in the horizontal direction due to the warehouse layout, we introduce a bias factor ($\beta_{bias}$, `bias_factor`) to weight the horizontal priority sum, giving it an extra competitive advantage. Therefore, the final horizontal priority $P'_{H}$ used for comparison is:

$$
P'_{H} = P_{H} \times \beta_{bias}
$$

#### 3. Decision Process

The controller's decision process is as follows:
1.  **Minimum Green Time Check**: To prevent frequent signal changes at the intersection due to rapid traffic fluctuations (which would cause robots to repeatedly accelerate and decelerate, wasting energy), the controller first checks if a minimum green time ($T_{min\_green}$) has elapsed since the last direction change. If not, the current direction is maintained.
2.  **Priority Comparison**: If the minimum green time has been met, the controller calculates the weighted horizontal priority $P'_{H}$ and the vertical priority $P_{V}$.
3.  **Special Case Handling**:
    - If there are no waiting robots in one direction, the right-of-way is immediately given to the other direction that has robots.
    - If there are no robots in either direction, the current state is maintained.
4.  **Final Decision**: In the general case, the controller compares $P'_{H}$ and $P_{V}$ and assigns the right-of-way to the direction with the higher priority sum.

$$
\text{Direction} = 
\begin{cases} 
\text{Horizontal,} & \text{if } P'_{H} \geq P_{V} \\
\text{Vertical,} & \text{if } P'_{H} < P_{V}
\end{cases}
$$

Through this mechanism, the `QueueBasedController` can respond reasonably and efficiently to real-time traffic demands while considering stability (minimum green time) and layout characteristics (bias factor).

## 3.3.3 Baseline Controller Parameter Settings

To ensure the validity and reproducibility of the experiments, this study has clearly defined and standardized the parameters used by the two baseline controllers. These parameters were selected based on experience from preliminary experiments and are intended to allow the controllers to exhibit reasonable and stable performance in general scenarios.

### 1. TimeBasedController

The logic of this controller is driven entirely by a fixed time cycle, and its parameters are set as follows:

| Parameter Name          | Default Value | Unit  | Description                                                                                             |
| ----------------------- | ------------- | ----- | ------------------------------------------------------------------------------------------------------- |
| `horizontal_green_time` | 70            | ticks | The duration of the green light for the horizontal direction. Due to the warehouse layout, the main horizontal thoroughfares carry heavier east-west traffic, so a longer passage time is given. |
| `vertical_green_time`   | 30            | ticks | The duration of the green light for the vertical direction.                                             |
| **Total Cycle Length**  | **100**       | **ticks** | **A complete signal cycle (`70 + 30`).**                                                                |

### 2. QueueBasedController

This controller makes decisions based on real-time traffic conditions, and its parameters involve the sensitivity of decisions and preferences for different tasks.

| Parameter Name       | Default Value                                                                     | Unit/Type    | Description                                                                                                                                                                                          |
| -------------------- | --------------------------------------------------------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `min_green_time`     | 1                                                                                 | ticks        | Minimum green time. A very small value is set to prevent the signal from "oscillating" too frequently between two conflicting requests, while still maintaining the controller's rapid response to traffic changes. |
| `bias_factor`        | 1.5                                                                               | float (multiplier) | Horizontal direction bias factor. This multiplier is applied to the weighted queue calculation for the horizontal direction to compensate for the naturally higher traffic flow, preventing the vertical direction from too frequently preempting the right-of-way due to a few high-priority robots. |
| `priority_weights`   | `{"delivering_pod": 3.0, "returning_pod": 2.0, "taking_pod": 1.0, "idle": 0.5}` | Dictionary   | Task priority weights. This dictionary defines the importance of robots in different task states. For example, a robot delivering goods to complete an order (`delivering_pod`) has a weight 6 times that of an idle (`idle`) robot. |

## 3.4 Deep Reinforcement Learning Controller Design

To address the highly dynamic and complex nature of internal traffic in RMFS, this study employs Deep Reinforcement Learning (DRL) to develop intelligent traffic controllers. DRL combines the powerful feature extraction capabilities of deep learning with the decision-making optimization framework of reinforcement learning, enabling an agent to learn effective control policies directly from high-dimensional raw sensory data.

Traditional traffic control methods, whether fixed-phase or rule-based heuristic algorithms, often struggle to achieve global optimality when faced with complex and non-linear traffic patterns. DRL methods offer a more adaptive solution, where the controller (agent) can autonomously learn a behavior policy that maximizes long-term cumulative rewards through continuous trial-and-error interactions with the simulation environment, without relying on manually designed complex rules.

This section will detail the architecture of two DRL controllers designed for this study:

1.  **Deep Q-Network (DQN)**: As a mature and widely used DRL algorithm, DQN serves as a strong **baseline** for measuring the relative performance of the new method proposed in this study.
2.  **Neuroevolution Reinforcement Learning (NERL)**: This is the **core contribution** of this study. This method combines the policy representation of neural networks with the global search capabilities of evolutionary algorithms, aiming to overcome challenges that traditional DRL methods may face in terms of training stability and sample efficiency.

The following subsections will first explain the model architecture and operating principles of DQN and NERL, respectively, and then detail the common state space, action space, and reward function designs, which are the core elements constituting a DRL problem.

## 3.4.1 Deep Q-Network (DQN) Controller Design

The Deep Q-Network (DQN) is the **baseline** method used in this study to establish a traffic control policy. As a foundational algorithm in the field of deep reinforcement learning, DQN combines deep neural networks with classic Q-Learning, enabling it to handle high-dimensional state spaces. DQN was chosen as a baseline to evaluate the improvements offered by the proposed NERL method within a recognized and stable DRL framework.

The core idea of DQN is to learn an Action-Value Function, the Q-function. This function, $Q(s, a; \theta)$, is approximated by a neural network defined by parameters $\theta$, with the goal of predicting the expected cumulative reward for taking action $a$ in a given state $s$. The optimal Q-function, $Q^*(s, a)$, follows the Bellman Optimality Equation:

$$
Q^*(s, a) = \mathbb{E}_{s' \sim P(\cdot|s,a)} \left[ r + \gamma \max_{a'} Q^*(s', a') \right]
$$

where $r$ is the immediate reward, $\gamma$ is the discount factor representing the importance of future rewards, and $s'$ is the successor state. Once an accurate Q-function is learned, the agent can execute the optimal policy in any state $s$ by selecting the action $a$ that maximizes $Q(s, a; \theta)$.

### 1. Core Stability Mechanisms

To address the training instability that can arise when using non-linear function approximators like neural networks, the DQN architecture adopted in this study integrates two key techniques:

*   **Experience Replay**: Transition samples $(s_t, a_t, r_t, s_{t+1})$ generated from the controller's interaction with the environment are stored in a fixed-size memory buffer $\mathcal{D}$. During training, the algorithm randomly samples a minibatch of these experiences for learning, rather than using consecutive time-series samples. This breaks the temporal correlations between samples, making the training data more closely resemble an independent and identically distributed (i.i.d.) assumption, which significantly improves training stability.

*   **Target Network**: The algorithm maintains two separate neural networks. One is the **Policy Network**, with parameters $\theta$, used to select actions at each time step. The other is the **Target Network**, with parameters $\theta^-$. When calculating the Temporal Difference (TD) target, the target Q-value is computed by the target network, i.e., $y_i = r_i + \gamma \max_{a'} Q(s'_{i}, a'; \theta^-)$. The parameters $\theta^-$ of the target network are periodically (not every step) copied from the policy network's parameters $\theta$ ($\theta^- \leftarrow \theta$). This delayed update mechanism decouples the dependency between the target Q-value and the current Q-value, effectively suppressing oscillations and divergence that can occur during bootstrapping.

### 2. Learning Process

The training of DQN is performed by minimizing a loss function over a randomly sampled batch of transition experiences. The loss function $L_i(\theta_i)$ is defined as the Mean Squared Error (MSE) between the TD target and the output of the policy network:

$$
L_i(\theta_i) = \mathbb{E}_{(s, a, r, s') \sim U(\mathcal{D})} \left[ \left( \underbrace{r + \gamma \max_{a'} Q(s', a'; \theta_i^-)}_{\text{TD Target}} - \underbrace{Q(s, a; \theta_i)}_{\text{Current Q-Value}} \right)^2 \right]
$$

The gradient of this loss function is used to update the weights $\theta_i$ of the policy network via stochastic gradient descent (SGD) or its variants (like Adam).

### 3. Neural Network Architecture

The policy and target networks used in the DQN controller of this study are both Feed-Forward Neural Networks. The input layer dimension corresponds to the state space defined in **Section 3.4.3**, and the output layer dimension corresponds to the action space defined in **Section 3.4.4**. The network contains two hidden layers and uses ReLU as the activation function. Its specific architecture is as follows:

**Input Layer (17) → Fully Connected Layer (128) → ReLU → Fully Connected Layer (64) → ReLU → Output Layer (6)**

This architecture strikes a balance between the model's expressive power and computational efficiency, and is sufficient for the traffic control problem in this study.

**[Figure Suggestion: Figure 3.4.1 - DQN Training and Decision Flowchart]**

It is recommended to draw a diagram here that clearly illustrates the complete operational flow of DQN. The diagram should include the following two parallel loops:
1.  **Decision Loop (Agent-Environment Interaction)**:
    *   Receive state $s_t$ from the environment.
    *   The policy network $Q(s, a; \theta)$ receives $s_t$ and outputs Q-values for all actions.
    *   Select action $a_t$ using an $\epsilon$-greedy policy.
    *   Execute $a_t$ in the environment to get reward $r_t$ and new state $s_{t+1}$.
    *   Store the transition sample $(s_t, a_t, r_t, s_{t+1})$ in the experience replay memory $\mathcal{D}$.
2.  **Training Loop (Network Update)**:
    *   Randomly sample a batch of transition experiences from $\mathcal{D}$.
    *   Calculate the TD target using the target network $Q(s, a; \theta^-)$.
    *   Calculate the loss function for the policy network $Q(s, a; \theta)$.
    *   Perform gradient descent to update the weights $\theta$ of the policy network.
    *   Periodically copy the weights of the policy network to the target network ($\theta^- \leftarrow \theta$).

## 3.4.2 Neuroevolution Reinforcement Learning (NERL) Controller Design

Neuroevolution Reinforcement Learning (NERL) is the **core method** proposed in this study. This approach combines the global search capabilities of Evolutionary Algorithms (EA) with the non-linear function approximation power of neural networks. It aims to overcome challenges that traditional gradient-based DRL methods (like DQN) may encounter when dealing with sparse rewards and complex parameter spaces, such as unstable convergence or getting trapped in local optima.

Unlike DQN, which seeks to approximate a value function, neuroevolution directly optimizes in the **parameter space** of a policy. In the NERL framework, the weights and biases $\theta$ of a neural network controller (i.e., a policy $\pi_\theta$) are treated as an individual's **genotype**. The algorithm searches for the optimal policy parameters $\theta^*$ by applying evolutionary operations to a **population** of many individuals.

### 1. Evolutionary Process

The core process of NERL revolves around an "evaluate → select → reproduce" evolutionary cycle, which iterates to improve the overall performance of the population. Assume at generation $g$, there is a population $P_g = \{\theta_1, \theta_2, ..., \theta_N\}$ containing $N$ individuals.

1.  **Evaluation**: Each individual $\theta_i$ in the population is deployed in a separate instance of the simulation environment to perform a full evaluation episode. During this episode, the policy $\pi_{\theta_i}$ makes all decisions independently. After the episode, the individual's **Fitness Score** $F(\theta_i)$ is calculated based on macroscopic system performance metrics (as defined by the global reward in **Section 3.4.5**). This process is highly parallelizable, which can significantly reduce training time.

2.  **Selection**: Based on the calculated fitness scores of all individuals, the algorithm selects high-performing individuals from the current population $P_g$ to act as **parents** for generating the next generation. This study uses **Tournament Selection**, which strikes a good balance between selection pressure and maintaining population diversity.

3.  **Reproduction**: A new offspring population $P_{g+1}$ is generated by applying genetic operations to the parents. The main operations include:
    *   **Elitism**: To prevent losing the best solutions found so far during evolution, the top $k$ elite individuals with the highest fitness in each generation are directly and completely copied to the next generation population $P_{g+1}$.
    *   **Crossover**: Simulating biological reproduction, two individuals $\theta_a$ and $\theta_b$ are selected from the parents, and their parameter vectors are mixed to create a new offspring $\theta_c$. This study uses **Uniform Crossover**, where each parameter of the new individual is inherited from $\theta_a$ or $\theta_b$ with equal probability.
    *   **Mutation**: After crossover, a small random perturbation is applied to the parameters $\theta_c$ of the offspring to generate the final $\theta'_c$. This operation is key to maintaining population diversity and avoiding premature convergence. This study uses **Gaussian Mutation**, where a noise sampled from a Gaussian distribution $\mathcal{N}(0, \sigma^2)$ is added to each parameter with a certain mutation probability $p_m$, where $\sigma$ is the mutation strength.

By iteratively performing this cycle, the average fitness of the population steadily increases, eventually converging to a high-performance policy network capable of efficiently solving the complex traffic control problem.

### 2. Key Differences Between NERL and DQN

*   **Optimization Domain**: DQN optimizes in the **value function space** (learning the Q-function), whereas NERL searches directly in the **policy parameter space**.
*   **Optimization Mechanism**: DQN relies on gradient-based backpropagation, requiring dense reward signals and a differentiable loss function. NERL uses gradient-free black-box optimization, which is more robust to the properties of the reward function (such as sparsity or delay), making it particularly suitable for scenarios that evaluate global performance.
*   **Exploration Mechanism**: DQN explores by introducing randomness in the **action space** (e.g., $\epsilon$-greedy). NERL's exploration is inherently performed through crossover and mutation operations in the **parameter space**.

### 3. Neural Network Architecture

To ensure a fair and consistent comparison with the DQN baseline, the NERL controller uses the exact same neural network architecture. Its input and output dimensions correspond to the state and action spaces defined in **Section 3.4.3** and **Section 3.4.4**, respectively.

**[Figure Suggestion: Figure 3.4.2 - NERL Evolutionary Cycle Diagram]**

It is recommended to draw a cyclical diagram here to illustrate the core workflow of NERL. The diagram should include:
1.  **Initial Population $P_g$**: Shows multiple neural network individuals $\theta_i$.
2.  **Parallel Evaluation**: Each $\theta_i$ runs in an independent environment, and its fitness $F(\theta_i)$ is calculated.
3.  **Selection**: Parents are selected via tournament selection based on fitness scores.
4.  **Reproduction to Generate $P_{g+1}$**: Shows elitism, crossover, and mutation operations creating the new generation.
5.  Arrows should clearly point to the next stage, forming a complete evolutionary closed loop from $P_g$ to $P_{g+1}$.

## 3.4.3 State Space Design

The definition of the state space is a cornerstone of successful reinforcement learning. It must provide the agent with sufficient and meaningful information to make effective decisions, while avoiding the "Curse of Dimensionality" caused by an overly high-dimensional space. In the RMFS traffic control problem of this study, the state $s_t$ of any intersection at decision time $t$ is defined as a feature vector that comprehensively reflects its local traffic conditions and considers the potential impact of surrounding and downstream intersections.

Specifically, $s_t$ is a **17-dimensional continuous vector**, composed as follows:

**1. Local State - 8 dimensions**: Describes the real-time traffic information of the intersection where the controller is located.
    *   **Horizontal Direction**:
        *   $s_t[0]$: **Queue Length** - The number of robots waiting to pass through the intersection on the horizontal thoroughfare.
        *   $s_t[1]$: **First Vehicle Waiting Time** - If the queue is not empty, this is the time the first robot in the queue has been waiting; otherwise, it is 0.
        *   $s_t[2]$: **Average Waiting Time** - The average waiting time of all waiting robots in the horizontal direction.
        *   $s_t[3]$: **Downstream Saturation** - The queue length of the next intersection in the horizontal direction, used to predict the risk of potential spillback.
    *   **Vertical Direction**:
        *   $s_t[4]$ - $s_t[7]$: The corresponding four features for the vertical thoroughfare.

**2. Neighbor State - 8 dimensions**: Describes key information from the four neighboring intersections directly connected to the current one, helping the agent to understand the broader traffic situation.
    *   **Each of the four neighbors (up, down, left, right)** includes 2 dimensions of information:
        *   $s_t[8], s_t[9]$: **Upstream Neighbor** - Vertical queue length, horizontal queue length.
        *   $s_t[10], s_t[11]$: **Downstream Neighbor** - Vertical queue length, horizontal queue length.
        *   $s_t[12], s_t[13]$: **Left Neighbor** - Vertical queue length, horizontal queue length.
        *   $s_t[14], s_t[15]$: **Right Neighbor** - Vertical queue length, horizontal queue length.

**3. Global State - 1 dimension**: Introduces a macroscopic indicator to help the agent align local decisions with overall system goals.
    *   $s_t[16]$: **Average Picking Station Queue** - The average queue length at the entrance of all picking stations. This is a critical system-level metric, as picking stations are the ultimate bottleneck for the entire material flow.

### State Normalization

Since the physical units and numerical ranges of the 17 features described above vary (e.g., counts, time, ratios), feeding them directly into a neural network would cause features of different scales to have varying impacts on the gradients, leading to unstable training. Therefore, before feeding the state vector $s_t$ into the DRL model, this study employs an **Adaptive Normalization** technique. This technique dynamically tracks the running mean and standard deviation of each state feature during training and uses them to standardize the feature values to a distribution with a mean close to 0 and a standard deviation close to 1, thereby ensuring the stability and efficiency of model training.

## 3.4.4 Action Space Design

In contrast to the high-dimensional state space, this study designs a concise and intuitive discrete action space $\mathcal{A}$ for the DRL agent. At each decision-making moment, the controller can select one action $a_t \in \mathcal{A}$ from a set of **6 discrete actions**. These actions not only cover basic traffic signal phase control but also introduce the ability to dynamically adjust local speed limits for more refined traffic flow management.

The action set $\mathcal{A}$ is defined as $\{0, 1, 2, 3, 4, 5\}$, where each integer corresponds to a specific control command:

### 1. Basic Phase Control

This part of the actions is mainly responsible for managing the right-of-way at the intersection.

*   **Action 0 (`KEEP_CURRENT_PHASE`)**: **Maintain Current Phase**. This action keeps the current signal state of the intersection unchanged. This is the optimal choice when the existing traffic flow is smooth, or when the cost of changing the phase is higher than the potential benefit.
*   **Action 1 (`SWITCH_TO_VERTICAL_GREEN`)**: **Switch to Vertical Green**. This action forces the signal phase to a vertical green light and a horizontal red light, aiming to clear traffic pressure in the vertical direction.
*   **Action 2 (`SWITCH_TO_HORIZONTAL_GREEN`)**: **Switch to Horizontal Green**. This action forces the signal phase to a horizontal green light and a vertical red light, aiming to clear traffic pressure in the horizontal direction.

### 2. Dynamic Speed Control

To more proactively manage traffic flow and avoid cascading spillbacks at bottleneck intersections, the model can also execute the following actions to dynamically adjust the speed limit of robots leaving the intersection. These actions do not change the signal phase themselves.

*   **Action 3 (`SET_SPEED_NORMAL`)**: **Set Speed to Normal**. This restores the speed limit for robots departing from this intersection to the default value (1.0), typically used after traffic conditions have eased.
*   **Action 4 (`SET_SPEED_SLOW`)**: **Set Speed to Slow**. This reduces the speed limit to a slow speed (0.5), used to actively smooth traffic fluctuations when downstream congestion is anticipated.
*   **Action 5 (`SET_SPEED_VERY_SLOW`)**: **Set Speed to Very Slow**. This reduces the speed limit to a very slow speed (0.2), used to minimize the flow into a congested area when severe downstream congestion has already occurred.

### Decision Interval

All DRL controllers operate on a fixed decision interval of $T_{\text{decision}} = 10$ ticks. This means the controller evaluates the current state $s_t$ and selects a new action $a_t$ every 10 simulation time steps. During this interval, the intersection maintains the signal phase and speed limit set by the previous decision.

## 3.4.5 Reward Function Design

The reward function $R(s, a, s')$ is the critical bridge connecting an DRL agent's actions to its ultimate learning goal. It evaluates the quality of taking action $a$ in state $s$ and transitioning to state $s'$ through a scalar feedback signal. In this study, to systematically investigate the impact of different learning signals on model performance and behavior, we designed and implemented two distinct reward modes. These modes are intended to balance the guidance of immediate feedback with the globality of the final goal, and are applied to the training of different DRL controllers (see **Section 3.6.1** for details).

### 1. Step Reward

The step reward mode aims to provide the agent with a dense, immediate feedback signal, primarily used to guide the learning of the DQN controller. At the end of each decision interval $T_{\text{decision}}$, the system calculates a composite reward value $R_{\text{step}}$ based on local observational metrics of the intersection during that time period. This high-frequency feedback helps the agent to quickly learn basic traffic control heuristics.

$R_{\text{step}}$ is a linear combination of the following four weighted components:

$$
R_{\text{step}} = w_{\text{critical}} \cdot (R_{\text{flow}} - P_{\text{wait}} - P_{\text{energy}} - P_{\text{switch}})
$$

*   **Flow Reward ($R_{\text{flow}}$)**: A positive reward that encourages the controller to maximize throughput.
    $$
    R_{\text{flow}} = w_{\text{flow}} \times N_{\text{passed}}
    $$
    where $N_{\text{passed}}$ is the total number of robots that successfully passed the intersection during the decision interval.

*   **Waiting Time Penalty ($P_{\text{wait}}$)**: A negative reward that penalizes the total waiting time accumulated from queuing.
    $$
    P_{\text{wait}} = w_{\text{wait}} \times T_{\text{cumulative\_wait}}
    $$

*   **Energy Consumption Penalty ($P_{\text{energy}}$)**: A negative reward that penalizes the estimated energy consumption from waiting and acceleration/deceleration.
    $$
    P_{\text{energy}} = w_{\text{energy}} \times E_{\text{consumed}}
    $$

*   **Phase Switch Penalty ($P_{\text{switch}}$)**: A fixed negative reward triggered only when the signal phase changes, intended to prevent overly frequent and ineffective switching.

Additionally, $w_{\text{critical}}$ is a **critical intersection weighting factor**. For intersections near system bottlenecks like picking stations, this factor will be greater than 1, thus amplifying their reward signal and prompting the agent to prioritize learning to manage these key nodes.

### 2. Global Reward

Unlike the step reward, the global reward mode provides a sparse, delayed feedback signal and is the core evaluation metric for the NERL method. In this mode, the agent receives no immediate rewards during the entire evaluation episode. Only at the end of the episode does the system calculate a single reward value $R_{\text{global}}$ based on the final macroscopic performance indicators of the entire warehouse. This value also serves as the **fitness score** in NERL.

This mode forces the agent to learn a series of complex, coordinated behaviors that have a positive impact on the system's long-term, global objectives rather than just local metrics. $R_{\text{global}}$ is a weighted combination of the following core indicators:

$$
R_{\text{global}} = S_{\text{order}} - C_{\text{time}} - C_{\text{energy}} - P_{\text{spillback}}
$$

*   **Order Completion Score ($S_{\text{order}}$)**: The main positive reward, based on the number of orders completed within the specified time.
    $$
    S_{\text{order}} = w_{\text{order}} \times N_{\text{completed\_orders}}
    $$

*   **Total Time Cost ($C_{\text{time}}$)**: A negative reward that penalizes the total time spent from the creation to the completion of all orders.
    $$
    C_{\text{time}} = w_{\text{time}} \times T_{\text{total\_order\_time}}
    $$

*   **Total Energy Cost ($C_{\text{energy}}$)**: A negative reward that penalizes the total estimated energy consumption of the system during operation.
    $$
    C_{\text{energy}} = w_{\text{energy\_global}} \times E_{\text{total}}
    $$

*   **Spillback Penalty ($P_{\text{spillback}}$)**: A huge negative penalty. This penalty is applied if a severe spillback leading to system deadlock occurs during the evaluation, ensuring the agent learns to avoid catastrophic strategies.

## 3.5 Experimental Design and Evaluation Method

To objectively and quantitatively answer the core question of this research—whether our proposed deep reinforcement learning traffic control strategies have a significant advantage in improving warehouse system operational efficiency compared to traditional methods—this section details the overall experimental design, model training process, performance evaluation framework, and statistical analysis methods for the results.

A rigorous experimental design is the cornerstone for ensuring the reliability of research conclusions. To this end, we will establish a comparative experimental matrix covering various control strategies and test them under a unified simulation environment and system load. All experiments will follow a standardized training and evaluation process to eliminate interference from irrelevant variables, ensuring that comparisons between different algorithms are fair and meaningful.

The structure of this section is as follows:
- **3.5.1 Training Configuration and Experimental Groups**: Defines all controller types (experimental groups) included in the experiment and describes the hardware and software environment configurations used for training.
- **3.5.2 Model Training Process**: Details the specific training steps for the DRL models (DQN and NERL) to ensure the reproducibility of the experiments.
- **3.5.3 Evaluation Method and Comparison Framework**: Explains the standardized process used for final performance evaluation after model training is complete, and the unified framework for horizontal comparison of all experimental groups.
- **3.5.4 Statistical Analysis and Results Validation**: Describes the statistical methods that will be used to analyze the experimental data to scientifically verify the significance of performance differences between different strategies.

## 3.6.1 Experimental Design and Group Definition

To systematically evaluate the performance of different traffic control strategies, this study designed a comparative experiment involving twelve independent experimental groups. This design aims to comprehensively compare the performance of the two deep reinforcement learning methods proposed in this study (DQN and NERL) under different reward modes and hyperparameter configurations against two heuristic baseline controllers.

### Experimental Group Definitions

All experimental groups are run in the standardized warehouse simulation environment described in **Section 3.2.1**, with the only variable being the traffic controller used at the intersections and its specific configuration. The detailed definitions of each experimental group are shown in the table below.

**Table 3.6.1: Experimental Group Definitions and Descriptions**

| Group | Controller Type | Reward Mode | NERL Variant | NERL Eval Duration (ticks) | Category | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `TimeBased` | - | - | - | Baseline | Static controller with fixed time cycles |
| 2 | `QueueBased` | - | - | - | Baseline | Dynamic reactive controller based on real-time queue length |
| 3 | `DQN` | `step` | - | - | DRL | DQN trained with step reward (see Section 3.6.2 for params) |
| 4 | `DQN` | `global` | - | - | DRL | DQN trained with global reward (see Section 3.6.2 for params) |
| 5 | `NERL` | `step` | **A (Exploratory)** | 3,000 | DRL | High mutation rate, short evaluation duration (see Section 3.6.2 for params) |
| 6 | `NERL` | `global` | **A (Exploratory)** | 3,000 | DRL | High mutation rate, short evaluation duration (see Section 3.6.2 for params) |
| 7 | `NERL` | `step` | **B (Exploitative)** | 3,000 | DRL | Low mutation rate, short evaluation duration (see Section 3.6.2 for params) |
| 8 | `NERL` | `global` | **B (Exploitative)** | 3,000 | DRL | Low mutation rate, short evaluation duration (see Section 3.6.2 for params) |
| 9 | `NERL` | `step` | **A (Exploratory)** | 8,000 | DRL | High mutation rate, long evaluation duration (see Section 3.6.2 for params) |
| 10 | `NERL` | `global` | **A (Exploratory)** | 8,000 | DRL | High mutation rate, long evaluation duration (see Section 3.6.2 for params) |
| 11| `NERL` | `step` | **B (Exploitative)** | 8,000 | DRL | Low mutation rate, long evaluation duration (see Section 3.6.2 for params) |
| 12| `NERL` | `global` | **B (Exploitative)** | 8,000 | DRL | Low mutation rate, long evaluation duration (see Section 3.6.2 for params) |

### NERL Variant Parameter Details

To investigate the impact of the balance between "Exploration" and "Exploitation" during the evolutionary process on the final policy performance, this study designed two NERL variants with different evolutionary hyperparameters. The core difference lies in the settings of the mutation operation:

- **Variant A (Exploratory)**: This configuration aims to promote a broad search in the parameter space. It is set with a higher mutation rate (`mutation_rate = 0.2`) and a larger mutation strength (`mutation_strength = 0.1`). This gives offspring individuals a greater potential to jump out of the neighborhood of existing solutions and discover new, potentially better policies, but it may also come with the risk of slower convergence.

- **Variant B (Exploitative)**: This configuration focuses on fine-tuning already discovered better solutions. It uses a lower mutation rate (`mutation_rate = 0.1`) and a smaller mutation strength (`mutation_strength = 0.05`). This conservative mutation strategy helps with the stable convergence of the policy but may also increase the risk of getting stuck in a local optimum.

Furthermore, to study the effect of the adequacy of individual policy evaluation on learning outcomes, each NERL variant will be trained and evaluated under two different evaluation durations: `3,000` ticks and `8,000` ticks.

### Hardware and Software Configuration

To ensure the consistency and reproducibility of the experimental results, all experiments were conducted in a standardized environment. Detailed information on the hardware and software stack has been provided in **Section 3.2.3**.

## 3.5.2 Model Training Process

To ensure that the DRL models can fully learn and converge to a relatively optimal policy, and to guarantee a fair comparison between different models, this study has designed a standardized model training process. This process details every step from model initialization to final model saving.

### 1. DQN Training Process (for groups 3, 4)

The training of DQN is an online, continuous learning process. A single complete DQN training experiment follows this procedure:

1.  **Initialization**:
    a. Create a `DQNController` instance based on the hyperparameters defined in Section `3.4.4` and the reward mode (`step` or `global`) specified for the experimental group.
    b. Create an instance of the `Warehouse` simulation environment.

2.  **Training Loop**:
    a. Start a simulation lasting for `N = 200,000` time steps (ticks).
    b. At each time step `t`, the `IntersectionManager` iterates through all intersections.
    c. For each intersection `i`:
        i. The controller gets the current state `s_t` from the environment.
        ii. An action `a_t` is selected using the policy network and an ε-greedy strategy.
        iii. Action `a_t` is executed, the environment transitions to the next state `s_{t+1}`, and the `UnifiedRewardSystem` calculates the immediate reward `r_t` (this reward is 0 in `global` mode).
        iv. The experience tuple `(s_t, a_t, r_t, s_{t+1})` is stored in the experience replay memory.
    d. **Experience Replay**: Every `k=32` time steps, a batch of experiences is randomly sampled from memory for learning.
    e. **Target Network Update**: Every `M=1,000` time steps, the weights of the policy network are copied to the target network.

3.  **Model Saving**: After the training is fully completed, the final weights of the policy network are saved as the final model.

### 2. NERL Training Process (for groups 5-12)

The training of NERL is a generational, off-policy learning process. Its core procedure is uniform for all NERL groups but incorporates different hyperparameters according to the specific group configuration.

1.  **Initialization**:
    a. Create a `NEController` instance based on Section `3.4.4` and the specific experimental group definition (5-12). This step determines the following key hyperparameters:
        - **Reward Mode**: `step` or `global`.
        - **Mutation Variant**: **A (Exploratory)** or **B (Exploitative)**, which determines the values of `mutation_rate` and `mutation_strength`.
        - **Evaluation Ticks**: `3,000` or `8,000`.
    b. The controller randomly initializes a population of `20` network individuals.

2.  **Evolutionary Loop**:
    a. Start an evolution lasting for `G = 30` generations.
    b. In each generation `g`:
        i. **Parallel Evaluation**: For the `20` individuals in the population, `20` independent, parallel simulation environments are launched.
        ii. Each individual `j` runs a full evaluation episode in its dedicated environment. The duration of the episode is determined by the `eval_ticks` parameter of that experimental group (`3,000` or `8,000` ticks).
        iii. After the episode ends, the `UnifiedRewardSystem` calculates the fitness score `f_j` for individual `j` based on the reward mode (`step` or `global`) specified for the group.
        iv. **Evolutionary Operations**: Once the fitness scores for all individuals have been calculated, the controller performs a full evolutionary operation (selection, crossover, mutation) based on the group's mutation variant (`A` or `B`) to generate a new offspring population.
        v. The new offspring population becomes the starting population for the next generation `g+1`.

3.  **Model Saving**:
    a. At the end of each generation, the algorithm saves the individual with the highest fitness in that generation as the best model of that generation.
    b. After all `30` generations of evolution are complete, the model with the highest fitness score across all generations is selected from all the saved best models and is designated as the final model for that experimental group.

## 3.6.2 DRL Model Hyperparameter Settings

To ensure the reproducibility of the DRL experiments and the validity of their results, this section details the key hyperparameters used in training the `DQN` and `NERL` controllers. These parameters were set based on preliminary convergence and stability experiments and were held constant during the formal training period.

### 1. DQN-Specific Hyperparameters

The following table lists the main hyperparameters used during the training of the `DQN` controller (experimental groups 3, 4).

| Parameter Name        | Code Variable          | Value   | Description                                                               |
| :-------------------- | :--------------------- | :------ | :------------------------------------------------------------------------ |
| Learning Rate         | `learning_rate`        | 5e-4    | The learning rate for the Adam optimizer.                                 |
| Discount Factor (Gamma) | `gamma`                | 0.99    | The discount factor for future rewards. A value closer to 1 means more emphasis on long-term returns. |
| Initial Epsilon       | `epsilon`              | 1.0     | The probability of choosing a random action at the beginning of training. |
| Minimum Epsilon       | `epsilon_min`          | 0.01    | The lower bound for the epsilon decay.                                    |
| Epsilon Decay Rate    | `epsilon_decay`        | 0.9995  | The exponential decay rate by which epsilon is multiplied after each training step. |
| Replay Memory Size    | `memory_size`          | 100,000 | The maximum number of $(s, a, r, s')$ transition samples to store.       |
| Batch Size            | `batch_size`           | 1,024   | The number of samples to draw from memory for each network update.        |
| Target Network Update Freq. | `target_update_freq` | 1,000   | The frequency (in training **steps**) at which the policy network's weights are copied to the target network. |

### 2. NERL-Specific Hyperparameters

The following table lists the main hyperparameters used during the evolution of the `NERL` controller (experimental groups 5-12). The mutation rate and mutation strength differ according to the **Exploratory (A)** and **Exploitative (B)** variants defined in **Section 3.6.1**.

| Parameter Name        | Code Variable          | Variant A (Exploratory) | Variant B (Exploitative) | Description                                                     |
| :-------------------- | :--------------------- | :---------------------- | :----------------------- | :-------------------------------------------------------------- |
| Population Size       | `population_size`      | 20                      | 20                       | The number of individuals (neural networks) in each generation. |
| Elite Ratio           | `elite_ratio`          | 0.1                     | 0.1                      | The proportion of the highest-fitness individuals directly preserved in each generation. |
| Tournament Size       | `tournament_size`      | 3                       | 3                        | The number of individuals randomly compared in each tournament selection. |
| Mutation Rate         | `mutation_rate`        | **0.2**                 | **0.1**                  | The base probability of an individual's genes (network weights) mutating. |
| Mutation Strength     | `mutation_strength`    | **0.1**                 | **0.05**                 | The standard deviation of the Gaussian mutation, controlling the magnitude of the mutation. |
| Evaluation Duration   | `eval_ticks`           | 3000 / 8000             | 3000 / 8000              | The duration (in ticks) for which each individual is evaluated. |

These hyperparameters collectively define the learning behavior of the two DRL methods and are an important basis for the subsequent experimental analysis and comparison of results.

## 3.5.3 Evaluation Method and Comparison Framework

After the DRL models have been trained according to the process described in Section `3.5.2`, a standardized evaluation procedure was designed to ensure that all controllers are compared on a fair and unbiased basis. This procedure aims to simulate a fixed, repeatable "test day" scenario and to quantify the performance of each control strategy using a predefined set of Key Performance Indicators (KPIs).

### 1. Standardized Evaluation Process

For each experimental group defined in Section `3.5.1` (including the two baseline controllers and the four trained DRL controllers), we will execute the following standardized evaluation procedure:

1.  **Model Loading**: For the DRL experimental groups, load their corresponding final trained models and set them to pure **Inference Mode**. In this mode, the ε-greedy exploration of DQN will be turned off (ε=0), and NERL will fixedly use its historically best-performing individual for decision-making.
2.  **Environment Reset**: Initialize a simulation environment that is identical to the one used during training but with a set of **fixed random seeds that were never used in training**. This ensures that all controllers face the exact same initial conditions, the same order sequence, and the same random events, thus eliminating interference from randomness.
3.  **Execution of Evaluation**: In the standardized environment, run a single, complete simulation of a fixed duration (e.g., `T_{eval} = 50,000` ticks).
4.  **Data Logging**: During the simulation, the `PerformanceReportGenerator` will record time-series data for all key performance indicators at fixed intervals (e.g., every 10 ticks).
5.  **Repeated Execution**: To eliminate the impact of extreme random events in a single run and to obtain more statistically significant results, the above steps 2-4 will be **repeated `K` times** (e.g., `K=10`) for each experimental group, using a different but shared set of random seeds for each run. The final performance will be the average of these `K` runs.

### 2. Performance Comparison Framework

After the `K` repeated evaluation runs are completed, we will aggregate and compare the data for each experimental group. The comparison framework will revolve around the Key Performance Indicators defined in Section `3.2.4`, which can be grouped into three main categories:

**A. Core Efficiency Indicators**
These indicators directly reflect the system efficiency that is of primary interest in this study.
- **Total Energy Consumption**: Evaluates the energy efficiency of the system; lower is better.
- **Completed Orders Count**: Measures the total output of the system in a fixed time; higher is better.

**B. Process Quality Indicators**
These indicators indirectly reflect the smoothness of system operation and the quality of service.
- **Average Order Processing Time**: Measures the system's response speed; lower is better.
- **Average Intersection Waiting Time**: Directly measures the effectiveness of the traffic control strategy; lower is better.
- **Total Stop-and-Go Count**: Reflects the smoothness of traffic flow; lower is better.

**C. Resource Utilization Indicators**
- **Average Robot Utilization**: Reflects the degree to which robot resources are utilized to achieve the output.

Finally, the average KPI data for all experimental groups will be organized into a comprehensive performance comparison table for in-depth analysis and discussion in the next chapter. Additionally, the collected time-series data will be plotted to visually demonstrate the dynamic behavior differences between the various strategies during the simulation process.

## 3.5.4 Statistical Analysis and Results Validation

To ensure that the conclusions of this study are based not just on descriptive mean comparisons but on a more rigorous statistical foundation, we will use Hypothesis Testing to verify whether the observed performance differences between different control strategies are statistically significant. This step is crucial for distinguishing between genuine performance improvements and accidental results caused by random fluctuations.

### 1. Hypothesis Testing Method

Since we conducted `K` independent repeated evaluations for each experimental group, this provides us with multiple sets of sample data. When comparing the performance of two different experimental groups (e.g., DQN-step vs. QueueBased) on a specific performance indicator (e.g., total energy consumption), we will use the **Independent Samples t-test**.

The basic procedure of the t-test is as follows:
1.  **Formulate the Null and Alternative Hypotheses**:
    - **Null Hypothesis (\\(H_0\\))**: There is no difference in the true mean of the indicator between the two control strategies. For example, \\(\mu_{DQN} = \mu_{QueueBased}\\).
    - **Alternative Hypothesis (\\(H_1\\))**: There is a difference in the true mean of the indicator between the two control strategies. For example, \\(\mu_{DQN} \neq \mu_{QueueBased}\\).

2.  **Set the Significance Level**:
    - We will adopt the conventional Significance Level of \\(\alpha = 0.05\\). This means we accept a maximum probability of 5% for incorrectly rejecting the null hypothesis (a Type I error).

3.  **Calculate the p-value**:
    - The **p-value** is calculated using the t-test. The p-value represents the probability of observing the current sample data, or more extreme data, given that the null hypothesis is true.

### 2. Interpretation of Results and Conclusion

Based on the calculated p-value, we will make the following interpretations:
- **If p < 0.05**: We will **reject the null hypothesis**. This means the observed performance difference is statistically significant, and we can be 95% confident that there is a real performance difference between the two strategies.
- **If p ≥ 0.05**: We will **fail to reject the null hypothesis**. This means the observed performance difference is not statistically significant and is likely due to random factors. We do not have sufficient evidence to claim a real difference between the two strategies.

By conducting t-tests on all key performance indicators and core experimental group pairings (e.g., DRL vs. baselines), we can provide strong statistical support for the experimental results analysis in Chapter 4, leading to more reliable and persuasive research conclusions. 