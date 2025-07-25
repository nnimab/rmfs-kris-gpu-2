# Chapter 3: Methodology

## 3.1 Problem Definition

In modern automated warehouses utilizing Robotic Mobile Fulfillment Systems (RMFS), increasing order volumes and higher robot deployment densities have made traffic congestion a core bottleneck constraining overall operational efficiency. A large number of robots executing tasks within a limited network of aisles, particularly at intersections, are highly prone to conflicts and waiting due to improper right-of-way coordination. This triggers a series of cascading negative effects, including delays in order fulfillment, energy waste from idle robot waiting, and a decline in overall system throughput.

Therefore, the central problem of this research is: **How to design an effective and adaptive traffic control strategy to dynamically regulate right-of-way at intersections, thereby minimizing robot waiting times and overall energy consumption, and ultimately enhancing the operational efficiency of the entire warehouse system?**

To answer this question, it is essential to first construct an experimental platform capable of accurately simulating these challenges. The experimental environment and system architecture detailed in this chapter constitute a high-fidelity testbed tailored for this core problem. Its purpose is to provide a stable, controllable, and quantifiable foundation for the implementation, training, and comparison of different control algorithms in subsequent chapters.

## 3.2 Experimental Environment and System Architecture

To effectively validate and compare the Neuroevolution Reinforcement Learning (NERL) traffic control strategy proposed in this study with other baseline methods, it is imperative to construct a high-fidelity simulation platform that accurately reflects the challenges of real-world warehouse operations. This platform serves not only as a testbed for the algorithms but also as a prerequisite for ensuring that all comparisons are conducted on a fair, controllable, and quantifiable basis.

This section provides a comprehensive overview of this experimental platform, sequentially covering five core components:
- **3.2.1 Warehouse Simulation Environment Design**: Details the physical layout and network structure of the simulated world, including core entity components such as robots, pods, and workstations.
- **3.2.2 Traffic Control System Architecture**: Delves into the software architecture designed for algorithm integration and evaluation, explaining how the system drives decisions, executes control, and triggers learning.
- **3.2.3 Experimental Hardware and Software Configuration**: Lists the specific hardware specifications and software libraries used for all simulation and training experiments.
- **3.2.4 Definition of Performance Evaluation Metrics**: Clearly defines the Key Performance Indicators (KPIs) used to measure the effectiveness of different control strategies, which serve as the basis for the experimental results analysis in subsequent chapters.
- **3.2.5 Robot Physical Model and Energy Consumption**: Details the robot's physical model and the method for calculating its energy consumption in the simulation, providing a physical foundation for energy efficiency evaluation.

Through this section, the reader will gain a complete understanding of the foundational environment and evaluation criteria for the experiments conducted in this research.

### 3.2.1 Warehouse Simulation Environment Design

To effectively evaluate traffic control strategies, this study first constructed a high-fidelity warehouse simulation environment. This environment not only defines the physical layout but also includes various dynamic entities and their interaction rules, collectively forming a complex Robotic Mobile Fulfillment System (RMFS). This section details its design.

#### 1. Physical Environment and Layout

The simulated warehouse is built on a two-dimensional discrete grid, where each grid cell has a specific function. The overall layout adopts a functional zoning design to ensure an orderly operational flow.

-   **Central Storage Area**: Located in the center of the warehouse, this area is densely packed with **Pod Locations**. The aisles in this area are designed as strict **One-way Aisles**, with the flow directions of horizontal and vertical aisles alternating. This design significantly simplifies the complexity of traffic management at a physical level, aiming to reduce potential conflicts from robots traveling in opposite directions.
-   **Workstation Area**: Distributed on both sides of the warehouse. One side features **Picking Stations**, which are the exit points for order fulfillment, while the other side has **Replenishment Stations**, the entry points for goods into the system.
-   **Charging Stations**: Scattered within the storage area, converted from some pod locations, for robots to charge autonomously.

**【圖表建議：圖 3.2.1 - 倉儲佈局示意圖】**
為直觀展示佈局，建議此處插入一張示意圖，用不同顏色標示出儲存區、揀貨區、補貨區與充電站，並用箭頭清晰標示出單向通道的流動方向。

#### 2. Core Entities and Lifecycles

The dynamic behavior of the system is driven by interactions between several core entities.

-   **Robot**: As the most central active unit in the system, the robot has a complex state machine to manage its workflow, including states such as `idle`, `taking_pod`, `delivering_pod`, `station_processing`, and `returning_pod`. This study establishes a detailed physical and energy model for the robot. Its energy consumption calculation considers not only the load but also startup costs and regenerative braking (energy recovery during braking), providing a solid basis for energy efficiency evaluation. Additionally, robots have priority-based autonomous obstacle avoidance logic, allowing them to resolve local conflicts to some extent on their own.

**【圖表建議：圖 3.2.2 - 機器人狀態轉換圖】**
為清晰展示機器人的工作流程，建議此處插入一張 UML 狀態機圖，描繪其核心狀態以及觸發狀態轉換的事件（如「分配新任務」、「到達工作站」等）。

-   **Pod**: The mobile carrier for storing stock-keeping units (SKUs). Each pod can hold multiple types of SKUs and records the current quantity and replenishment threshold for each SKU. When the stock level falls below the threshold, the system automatically triggers a corresponding replenishment task.

-   **Station**: The node for human-robot collaboration. After a robot delivers a pod to a station, the system simulates the delay of a worker picking or replenishing items. To handle high traffic, stations are also designed with a dynamic path adjustment mechanism, activating a longer backup path to alleviate congestion when too many robots are present.

**【圖表建議：圖 3.2.3 - 倉儲標示圖】**

#### 3. Orders and Task Flow

The simulation is driven by orders. An **Order** represents a customer request and contains multiple SKUs to be picked. The system breaks down an order into one or more **Jobs**. The core of a job is "transporting a specified pod to a specified workstation," which is the smallest work unit that can be directly assigned to a robot. The entire process is as follows:
1.  The system receives an order.
2.  The SKUs required for the order are located on specific pods.
3.  The system generates one or more jobs and places them in the job queue.
4.  An idle robot takes a job from the queue and begins its work cycle of picking up, delivering, and returning the pod.
5.  When all SKUs for an order have been successfully delivered to the workstation, the order is marked as complete.

#### 4. Intersection Design and Classification

In addition to the macroscopic layout, this study provides a clear classification and definition of the microscopic traffic nodes within the warehouse—the intersections. This is crucial for the subsequent controller design.

-   **Standard Intersection**: This is the basic unit that constitutes the main body of the warehouse traffic network, formed by the convergence of two perpendicular one-way aisles. All intersections not otherwise specified fall into this category.

-   **Critical Intersection**: Based on their strategic importance in the warehouse layout, some intersections are marked as "critical." These are traffic nodes on the access or egress paths directly connected to **Workstations (Picking or Replenishment Stations)**. They are the mandatory routes for entering and exiting workstations and constitute the primary traffic **bottlenecks** of the entire warehouse system. The efficiency of managing these intersections directly affects workstation throughput and robot queue lengths, and may trigger **spillback** phenomena that propagate into the storage area. Therefore, in the design of the reinforcement learning reward function (see Section 3.4.5), these intersections will be given a higher weight to guide the agent to prioritize learning their effective management.

**【圖表建議：圖 3.2.4 - 倉儲交叉路口分類與關鍵路口標示圖】**
為直觀展示不同路口的地理分佈，建議此處插入一張與圖 3.2.1 風格一致的倉儲佈局圖。在圖中，應使用不同的符號或顏色清晰標示出標準十字路口與所有關鍵路口的位置，特別是與揀貨站和補貨站的鄰接關係。 

### 3.2.2 Traffic Control System Architecture

To enable flexible integration and fair comparison of different traffic control algorithms, this study designed a modular software architecture based on the **Strategy Pattern** and **Factory Pattern**. The core of this architecture is the separation of the "decision algorithm" from the "system execution framework," ensuring that all strategies, from simple rule-based logic to complex deep reinforcement learning models, operate and are evaluated on the same foundation. The system consists of three main components:

#### 1. `TrafficController` (Abstract Base Class for Traffic Controllers)
This Abstract Base Class (ABC) defines a unified interface that all traffic control strategies must adhere to. Its most critical method is `get_direction(intersection, tick, warehouse)`, which receives the current detailed state of an intersection (local information) and the state of the entire warehouse system (global information), and returns a traffic decision for that intersection (e.g., `"Horizontal"` or `"Vertical"`). By forcing all controllers to implement this interface, the system ensures consistency in how different algorithms are called. Additionally, the base class integrates standardized statistical data collection to record various performance metrics.

#### 2. `TrafficControllerFactory` (Controller Factory)
This class employs the factory design pattern and is responsible for dynamically creating instances of `TrafficController` subclasses based on external settings (e.g., the controller type specified in an experiment configuration file). When the simulation core requires a controller, it only needs to provide a string identifier such as `"dqn"`, `"nerl"`, or `"time_based"`, and the factory returns a corresponding, initialized controller object. This design completely decouples the "creation logic" from the "usage logic" of the controllers, greatly enhancing the flexibility and scalability of the experimental workflow and allowing different control strategies to be switched without modifying any core simulation code.

#### 3. `IntersectionManager` (Intersection Manager)
The `IntersectionManager` is the central coordinator and execution engine of the entire traffic control system. Its operational flow forms a complete closed-loop control system:
1.  **Holds Controller Instance**: During the simulation initialization phase, the `IntersectionManager` obtains the required controller instance for the current experiment from the controller factory.
2.  **Drives Decision Loop**: At each time unit (tick) of the simulation, the manager iterates through all intersections in the warehouse.
3.  **Obtains Decision**: For each intersection, it calls the `get_direction()` method of the `TrafficController` instance to get the traffic command for that intersection.
4.  **Executes Decision**: Based on the command returned by the controller, the `IntersectionManager` updates the internal state of the intersection, such as changing the allowed direction of travel.
5.  **Triggers Model Training**: Specifically for reinforcement learning-based controllers (DQN/NERL), after the decision and execution steps are completed, the `IntersectionManager` will then call their `train()` method, providing the state transition that just occurred (State-Action-Reward-NextState) to the model, enabling it to learn and optimize from experience.

**【圖表建議：圖 3.2.1 - 交通控制系統運作序列圖】**

為使讀者能更直觀地理解此運作流程，強烈建議在此處插入一張 **UML 序列圖 (Sequence Diagram)**。該圖應清晰地展示從模擬器主迴圈 (`Simulation Loop`) 觸發，到 `IntersectionManager` 遍歷路口，再到 `TrafficController` 進行決策 (`get_direction`)，最後由 `IntersectionManager` 更新路口狀態 (`updateAllowedDirection`) 並觸發學習 (`train`) 的完整訊息傳遞順序。 

### 3.2.3 Experimental Hardware and Software Configuration

To ensure the reproducibility and validity of this research, all simulation, training, and evaluation experiments were conducted on a well-defined hardware platform and in a standardized software environment. This section details the relevant configurations.

#### Hardware Configuration

The computational tasks of this study were primarily divided into two parts: model training on a high-performance cloud platform, and development, debugging, and results analysis on a local machine.

##### Training Environment (Runpod Secure Cloud)
All computationally intensive model training tasks were performed on the Runpod cloud platform to leverage its powerful computational resources and accelerate the learning process.
- **CPU**: 42 vCPU
- **GPU**: 1 x NVIDIA GeForce RTX 4090
- **Memory (RAM)**: 83 GB

##### Development and Analysis Environment (User's Laptop)
Code development, preliminary testing, parameter tuning, and final data analysis and visualization were completed on a local computer.
- **CPU**: AMD Ryzen 9 6900HX
- **GPU**: NVIDIA GeForce RTX 3080 Ti
- **Memory (RAM)**: 16.0 GB

#### Software Configuration

The software environment was chosen to balance development efficiency, computational performance, and broad community support.
- **Operating System**:
    - **Training Environment**: Ubuntu 22.04 (in a `runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel` Docker container)
    - **Development Environment**: Microsoft Windows 11
- **Programming Language**: `Python 3.10`
- **Core Computational Libraries**:
    - `PyTorch` (version `2.1.0`): As the core deep learning framework, used to build and train the DQN and NERL neural network models.
    - `numpy` (version `1.24.4`): Provided the foundation for all numerical computations, widely used in state representation, reward calculation, etc.
    - `pandas` (version `2.0.3`): Primarily used for processing, storing, and analyzing experimental data.
- **Simulation and Analysis Tools**:
    - `networkx` (version `3.2.1`): Used to construct and analyze the warehouse's road network graph structure.
    - `scikit-learn` (version `1.5.2`): In this study, mainly used for preprocessing steps such as data normalization.
- **Visualization Libraries**:
    - `matplotlib` (version `3.7.2`): Used to generate static 2D plots like line charts and bar charts.
    - `seaborn` (version `0.13.2`): Built on top of matplotlib, providing more aesthetically pleasing and statistically-oriented visualizations like heatmaps.
- **System Tools**:
    - `psutil` (version `5.9.8`): Used to monitor system resource usage.


### 3.2.4 Definition of Performance Evaluation Metrics

To objectively and quantitatively evaluate the merits of different traffic control strategies, this study establishes a comprehensive set of Key Performance Indicators (KPIs). For clarity, we first define the following mathematical symbols:
- $R$: The set of all robots in the warehouse.
- $O_{\text{completed}}$: The set of all orders completed during the simulation period.
- $P$: The set of all events of robots passing through an intersection.
- $T_{\text{sim}}$: The total simulation duration, in units of $ticks$.

#### 1. Efficiency Metrics

**Total Energy Consumption**
This metric measures the overall energy efficiency of the system and is a core optimization target of this study. It is calculated as the sum of the energy consumed by all robot activities during the simulation period (see Section 3.2.5 for the detailed calculation model).
$$
E_{\text{total}} = \sum_{r \in R} E_r \quad (3-1)
$$
where $E_r$ represents the total energy consumption of a single robot $r$ throughout the simulation, in Energy Units (EU).

#### 2. Throughput Metrics

**Completed Orders Count**
This metric directly measures the total output of the system within a fixed time, reflecting its overall operational efficiency.
$$
N_{\text{orders}} = |O_{\text{completed}}| \quad (3-2)
$$

**Average Order Processing Time**
This metric measures the system's responsiveness in handling a single order. It is defined as the average time taken for all completed orders from their start to their completion.
$$
T_{\text{avg_order}} = \frac{1}{|O_{\text{completed}}|} \sum_{o \in O_{\text{completed}}} (t_{\text{complete}}(o) - t_{\text{start}}(o)) \quad (3-3)
$$
where $t_{\text{complete}}(o)$ and $t_{\text{start}}(o)$ are the completion and start times of order $o$, respectively, both in units of $ticks$.

**Average Intersection Waiting Time**
This metric directly reflects the coordination efficiency of the traffic control strategy. It calculates the average waiting time for each robot passing through an intersection.
$$
W_{\text{avg}} = \frac{1}{|P|} \sum_{p \in P} t_{\text{wait}}(p) \quad (3-4)
$$
where $|P|$ is the total number of times robots pass through intersections, and $t_{\text{wait}}(p)$ is the waiting time for a single passing event $p$, in units of $ticks$.

#### 3. Stability Metrics

**Total Stop-and-Go Count**
This metric reflects the smoothness of the traffic flow. Frequent stops and starts not only consume additional energy but also indicate unstable traffic flow.
$$
S_{\text{total}} = \sum_{r \in R} N_{\text{s-g}}(r) \quad (3-5)
$$
where $N_{\text{s-g}}(r)$ is the number of stop-and-go events for robot $r$.

### 3.2.5 Robot Physical Model and Energy Consumption

To ensure the realism and credibility of the simulation, this study establishes a robot model based on physical principles. This section details the physical unit system used in the simulation, the core parameters of the robot, and the energy consumption calculation model.

#### 1. Definition of Unit System

To unify physical calculations in the simulation, this study adopts the following consistent unit system:

- **Time**: The basic time unit in the simulation is the $tick$. According to the system settings, one $tick$ corresponds to $0.15$ seconds in the real world.
- **Distance**: One unit of length in the simulation corresponds to $1$ meter in the real world.
- **Mass**: The unit of mass in the simulation is kilograms (kg).
- **Velocity**: The unit is meters per second (m/s).
- **Acceleration**: The unit is meters per second squared (m/s²).
- **Energy**: Energy is calculated based on standard physical formulas. To maintain internal consistency in the simulation, we define its unit as the "Energy Unit (EU)," which is proportional to the Joule (J).

#### 2. Robot Physical Parameters

The following table details the physical parameters applied to all robot entities. These parameters are defined in `world/entities/robot.py` and remain constant throughout the simulation.

**【表格建議：表 3.2.1 - 機器人模型物理參數】**

| Parameter | Symbol | Value | Unit | Physical Meaning |
| :--- | :--- | :--- | :--- | :--- |
| Robot Mass | $m_{\text{robot}}$ | 1 | kg | Mass of the robot itself |
| Load Mass | $m_{\text{load}}$ | 0 | kg | Additional load when the robot carries goods |
| Gravity | $g$ | 10 | m/s² | Approximate value of Earth's gravitational acceleration |
| Friction Coefficient | $\mu$ | 0.3 | - | Rolling friction between the ground and wheels |
| Inertia Coefficient | $I$ | 0.4 | - | Inertial resistance experienced by the robot when accelerating |
| Startup Cost | $C_{\text{startup}}$ | 0.5 | EU | Additional energy cost to overcome static friction when starting from rest |
| Regenerative Braking Efficiency | $\eta_{\text{regen}}$ | 0.3 | - | Proportion of kinetic energy that can be recovered during braking (30%) |
| Maximum Speed | $v_{\text{max}}$ | 1.5 | m/s | The robot's maximum speed under no restrictions |

#### 3. Energy Consumption Calculation Model

The energy consumption model in this study not only considers basic movement energy but also integrates startup costs and regenerative braking mechanisms to more realistically reflect the energy characteristics of electric robots. Total energy consumption is calculated cumulatively based on the robot's different motion states.

**A. Constant Velocity Energy Consumption**
When a robot moves at a constant velocity $v$, its energy consumption primarily comes from overcoming friction.
$$
E_{\text{friction}} = (m_{\text{robot}} + m_{\text{load}}) \cdot g \cdot \mu \cdot v \cdot \Delta t \quad (3-6)
$$
where $\Delta t$ is one time step ($0.15$ seconds).

**B. Acceleration Energy Consumption**
When a robot accelerates with acceleration $a$, it needs to overcome inertia in addition to friction.
$$
E_{\text{accel}} = (m_{\text{robot}} + m_{\text{load}}) \cdot (g \cdot \mu + a \cdot I) \cdot \bar{v} \cdot \Delta t \quad (3-7)
$$
where $\bar{v}$ is the average velocity during that time step.

**C. Startup Cost**
When a robot starts moving ($v > 0$) from rest ($v_{\text{prev}} = 0$), a one-time, fixed startup cost is incurred.
$$
E_{\text{startup}} = C_{\text{startup}} \quad (3-8)
$$

**D. Regenerative Braking (Energy Recovery)**
When a robot brakes to a complete stop ($v = 0$) from a moving state ($v_{\text{prev}} > 0$), the system recovers a portion of the energy based on its change in kinetic energy.
$$
E_{\text{regen}} = \frac{1}{2} (m_{\text{robot}} + m_{\text{load}}) \cdot v_{\text{prev}}^2 \cdot \eta_{\text{regen}} \quad (3-9)
$$

**E. Total Energy Change**
Combining all the above, the total energy change $\Delta E_{\text{total}}$ for a robot in a single time step can be expressed as:
$$
\Delta E_{\text{total}} = E_{\text{movement}} + E_{\text{startup}} - E_{\text{regen}} \quad (3-10)
$$
where $E_{\text{movement}}$ corresponds to $E_{\text{friction}}$ or $E_{\text{accel}}$ depending on whether the robot is moving at a constant velocity or accelerating. The total energy consumption of the system is the cumulative sum of $\Delta E_{\text{total}}$ for all robots over all time steps.

## 3.3 Baseline Controller Design

To objectively and rigorously evaluate the performance of the deep reinforcement learning traffic control methods proposed in this study (detailed in Section 3.4), they must be compared against a set of representative and easily understandable baseline controllers. Baseline controllers provide a performance reference point, allowing us to quantify the actual improvements brought by more complex algorithms. An ideal baseline should reflect existing industry practices or intuitive solutions.

This study selects two different but representative logics to design the baseline controllers: one is a fixed-time controller that completely ignores real-time traffic conditions, and the other is a dynamic controller that reacts to the immediate demands of the intersection. These two represent the basic forms of static and dynamic control strategies, respectively, and can comprehensively measure the adaptability and superiority of reinforcement learning models in different traffic scenarios.

This section will detail the internal design principles, decision logic, and key parameters of the following two baseline controllers:

1.  **Time-Based Controller**: A static controller based on a fixed time cycle for switching right-of-way.
2.  **Queue-Based Controller**: A dynamic reactive controller that makes decisions based on the length of waiting queues at the intersection and the priority of tasks.

### 3.3.1 Time-Based Controller

The `TimeBasedController` is the most fundamental static traffic control strategy. Its core idea is derived from traditional urban traffic light systems, completely ignoring real-time traffic flow or any dynamic changes at the intersection. It relies solely on a pre-set, fixed time cycle to alternate the right-of-way between horizontal and vertical directions. The advantage of this method lies in its extreme simplicity and predictability, but its disadvantage is equally obvious—it cannot adapt to fluctuations in traffic demand, often causing unnecessary waiting during busy periods or wasting green time during sparse traffic.

#### Design Principle and Decision Logic

The operation of this controller is determined entirely by three parameters: horizontal green time ($T_{H\_green}$), vertical green time ($T_{V\_green}$), and the complete signal cycle length ($T_{cycle}$), which is the sum of the two.

$$
T_{cycle} = T_{H\_green} + T_{V\_green} \quad (3-11)
$$

At any given time tick in the simulation, the controller determines the current position in the signal cycle ($t_{pos}$) using the modulo operation:

$$
t_{pos} = \text{tick} \bmod T_{cycle} \quad (3-12)
$$

Based on the value of $t_{pos}$, the controller makes a decision on the direction of passage. If $t_{pos}$ is less than the horizontal green time $T_{H\_green}$, it grants the right-of-way to the horizontal direction; otherwise, it grants it to the vertical direction. The decision rule can be expressed as:

$$
\text{Direction} = 
\begin{cases} 
\text{Horizontal,} & \text{if } t_{pos} < T_{H\_green} \\
\text{Vertical,} & \text{if } t_{pos} \geq T_{H\_green}
\end{cases}
\quad (3-13)
$$

In our warehouse environment, since pods are mainly arranged along horizontal aisles, the frequency and volume of robot movement in the horizontal direction are much higher than in the vertical direction. To accommodate this characteristic, we assign a longer green time to the horizontal direction (e.g., $T_{H\_green} = 70$ ticks) and a relatively shorter green time to the vertical direction (e.g., $T_{V\_green} = 30$ ticks), aiming to achieve a preliminary traffic balance without considering real-time status.

---
**【圖表建議：圖 3.3.1 - 時間基礎控制器訊號週期示意圖】**

建議在此處插入一張時間軸圖，清晰地展示 $T_{cycle}$ 的構成，並標示出 $T_{H\_green}$ 和 $T_{V\_green}$ 的區間，以及在不同區間內對應的通行方向決策（Horizontal/Vertical）。

### 3.3.2 Queue-Based Controller

The `QueueBasedController` is a dynamic reactive control strategy designed to address the fundamental shortcoming of the time-based controller: its inability to perceive real-time traffic demand. This controller continuously monitors the waiting queues in both directions of an intersection and dynamically calculates the right-of-way based on the urgency of the tasks being performed by the robots. Compared to the static time-based controller, the queue-based controller can adapt more flexibly to changes in traffic flow, prioritizing the allocation of passage resources to the direction with more urgent demand.

#### Design Principle and Decision Logic

The core of this controller lies in quantifying and combining two key factors for decision-making: **number of robots** and **task priority**.

##### 1. Task Priority Weight System

Not all robot tasks in warehouse operations have the same level of importance. For example, a robot delivering a pod to a picking station, if delayed, will directly impact order fulfillment efficiency. In contrast, an empty robot heading to the pod area has a relatively lower task urgency. To reflect this difference, we define a set of priority weights ($W_{\text{priority}}$) for different robot states (`robot.current_state`):

| Robot State (`current_state`) | Task Description | Priority Weight ($W_{\text{priority}}$) |
| :--- | :--- | :---: |
| `delivering_pod` | Delivering a pod to a picking station | 3.0 |
| `returning_pod` | Returning a pod to the storage area | 2.0 |
| `taking_pod` | Going to the storage area to pick up a pod | 1.0 |
| `idle` | Idle or on standby | 0.5 |
| `station_processing` | Processing at a station | 0.0 |

##### 2. Direction Priority Calculation

For each direction at an intersection (Horizontal H or Vertical V), the controller calculates a weighted priority sum ($P_{H}$ or $P_{V}$). This value is the sum of the task priority weights of all waiting robots in that direction ($R_{dir}$). The formula is as follows:

$$
P_{\text{dir}} = \sum_{i \in R_{\text{dir}}} W_{\text{priority}}(i) \quad (3-14)
$$

where $W_{\text{priority}}(i)$ represents the priority weight corresponding to the current state of robot $i$.

Furthermore, considering the inherent higher traffic flow in the horizontal direction due to the warehouse layout, we introduce a bias factor ($\beta_{\text{bias}}$, `bias_factor`) to weight the horizontal priority sum, giving it an additional competitive advantage. Thus, the final horizontal priority $P'_{H}$ used for comparison is:

$$
P'_{H} = P_{H} \times \beta_{\text{bias}} \quad (3-15)
$$

##### 3. Decision Process

The controller's decision process is as follows:
1.  **Minimum Green Time Check**: To prevent frequent signal switching due to rapid changes in traffic conditions (which would cause robots to repeatedly accelerate and decelerate, wasting energy), the controller first checks if a minimum green time ($T_{\text{min_green}}$) has elapsed since the last direction change. If not, the current direction is maintained.
2.  **Priority Comparison**: If the minimum green time is met, the controller calculates the weighted horizontal priority $P'_{H}$ and the vertical priority $P_{V}$.
3.  **Special Case Handling**:
    - If either direction has no waiting robots, the right-of-way is immediately given to the other direction that has robots.
    - If both directions have no robots, the current state is maintained.
4.  **Final Decision**: In the general case, the controller compares $P'_{H}$ and $P_{V}$ and assigns the right-of-way to the direction with the higher priority sum.

$$
\text{Direction} = 
\begin{cases} 
\text{Horizontal,} & \text{if } P'_{H} \geq P_{V} \\
\text{Vertical,} & \text{if } P'_{H} < P_{V}
\end{cases}
\quad (3-16)
$$

Through this mechanism, the queue-based controller can respond reasonably and efficiently to real-time traffic demands while considering stability (minimum green time) and layout characteristics (bias factor).

### 3.3.3 Baseline Controller Parameter Settings

To ensure the validity and reproducibility of the experiments, this study clearly defines and standardizes the parameters used by the two baseline controllers. These parameters were selected based on empirical data from preliminary experiments, aiming for reasonable and stable performance in general scenarios.

#### 1. Time-Based Controller

The logic of this controller is driven entirely by a fixed time cycle, with parameters set as follows:

| Parameter Name | Default Value | Unit | Description |
| --- | --- | --- | --- |
| `horizontal_green_time` | 70 | ticks | Green light duration for the horizontal direction. Due to the warehouse layout, the horizontal main aisle carries heavier east-west traffic, thus it is given a longer passage time. |
| `vertical_green_time` | 30 | ticks | Green light duration for the vertical direction. |
| **Total Cycle Length** | **100**| **ticks** | **A complete signal cycle (`70 + 30`).** |

#### 2. Queue-Based Controller

This controller makes decisions based on real-time traffic conditions, and its parameters involve decision sensitivity and preference for different tasks.

| Parameter Name | Default Value | Unit/Type | Description |
| --- | --- | --- | --- |
| `min_green_time` | 1 | ticks | Minimum green time. A very small value is set to prevent the signal from "oscillating" too frequently between two conflicting requests, while still maintaining the controller's rapid response to traffic changes. |
| `bias_factor` | 1.5 | float (multiplier) | Horizontal direction preference factor. This multiplier is applied to the calculated weighted queue for the horizontal direction to compensate for its naturally higher traffic flow, preventing the vertical direction from too frequently preempting the right-of-way due to a small number of high-priority robots. |
| `priority_weights` | `{"delivering_pod": 3.0, "returning_pod": 2.0, "taking_pod": 1.0, "idle": 0.5}` | Dictionary | Task priority weights. This dictionary defines the importance of robots in different task states. For example, a robot delivering goods to complete an order (`delivering_pod`) has a weight 6 times that of an idle robot. |

## 3.4 Deep Reinforcement Learning Controller Design

To address the highly dynamic and complex nature of traffic within an RMFS, this study employs Deep Reinforcement Learning (DRL) to develop intelligent traffic controllers. DRL combines the powerful feature extraction capabilities of deep learning with the decision-making optimization framework of reinforcement learning, enabling an agent to learn effective control policies directly from high-dimensional raw sensory data.

Traditional traffic control methods, whether fixed-phase or rule-based heuristic algorithms, often struggle to achieve global optimality when faced with complex and non-linear traffic patterns. DRL methods offer a more adaptive solution, where the controller (agent) can autonomously learn a policy that maximizes long-term cumulative rewards through continuous trial-and-error interactions with the simulation environment, without relying on manually designed complex rules.

This section details the two DRL controller architectures designed for this study:

1.  **Deep Q-Network (DQN)**: As a mature and widely used DRL algorithm, DQN serves as a strong **baseline** for comparison, used to measure the relative performance of the novel method proposed in this study.
2.  **Neuroevolution Reinforcement Learning (NERL)**: This is the **core contribution** of this study. This method combines the policy representation of neural networks with the global search capabilities of evolutionary algorithms, aiming to overcome challenges that traditional DRL methods may face, such as training instability and sample inefficiency.

The following subsections will first explain the model architecture and operational principles of DQN and NERL, respectively, and then detail the common state space, action space, and reward function designs, which are the core elements of a DRL problem.

### 3.4.1 Deep Q-Network (DQN) Controller Design

The Deep Q-Network (DQN) is the **baseline** method used in this study to establish a traffic control policy. As a foundational algorithm in the field of deep reinforcement learning, DQN combines deep neural networks with classic Q-Learning, enabling it to handle high-dimensional state spaces. DQN was chosen as a baseline to evaluate the improvements offered by the proposed NERL method within a recognized and stable DRL framework.

The core idea of DQN is to learn an action-value function, the Q-function. This function, $Q(s, a; \theta)$, is approximated by a neural network defined by parameters $\theta$, with the goal of predicting the expected cumulative reward for taking action $a$ in a given state $s$. The optimal Q-function, $Q^*(s, a)$, follows the Bellman optimality equation:

$$
Q^*(s, a) = \mathbb{E}_{s' \sim P(\cdot|s,a)} \left[ r + \gamma \max_{a'} Q^*(s', a') \right] \quad (3-17)
$$

where $r$ is the immediate reward, $\gamma$ is the discount factor representing the importance of future rewards, and $s'$ is the successor state. Once an accurate Q-function is learned, the agent can execute an optimal policy in any state $s$ by selecting the action $a$ that maximizes $Q(s, a; \theta)$.

#### 1. Core Stability Mechanisms

To address the training instability that can arise when using non-linear function approximators like neural networks, the DQN architecture adopted in this study integrates two key techniques:

*   **Experience Replay**: The transition samples $(s_t, a_t, r_t, s_{t+1})$ generated from the controller's interaction with the environment are stored in a fixed-size memory buffer $\mathcal{D}$. During training, the algorithm randomly samples a minibatch of experiences from $\mathcal{D}$ for learning, rather than using consecutive time-series samples. This practice breaks the temporal correlations between samples, making the training data more closely resemble an independent and identically distributed (i.i.d.) assumption, which significantly improves training stability.

*   **Target Network**: The algorithm maintains two separate neural networks. One is the **policy network**, with parameters $\theta$, used to select actions at each time step. The other is the **target network**, with parameters $\theta^-$. When calculating the Temporal Difference (TD) target, the target Q-value is computed by the target network, i.e., $y_i = r_i + \gamma \max_{a'} Q(s'_{i}, a'; \theta^-)$. The parameters $\theta^-$ of the target network are periodically (rather than every step) copied from the policy network's parameters $\theta$ ($\theta^- \leftarrow \theta$). This delayed update mechanism decouples the dependency between the target Q-value and the current Q-value, effectively suppressing oscillations and divergence that may occur during bootstrapping.

#### 2. Learning Process

DQN training is performed by minimizing a loss function over a randomly sampled batch of transition samples. The loss function $L_i(\theta_i)$ is defined as the Mean Squared Error (MSE) between the TD target and the output of the policy network:

$$
L_i(\theta_i) = \mathbb{E}_{(s, a, r, s') \sim U(\mathcal{D})} \left[ \left( \underbrace{r + \gamma \max_{a'} Q(s', a'; \theta_i^-)}_{\text{TD Target}} - \underbrace{Q(s, a; \theta_i)}_{\text{Current Q-value}} \right)^2 \right] \quad (3-18)
$$

The gradient of this loss function is used to update the weights $\theta_i$ of the policy network via stochastic gradient descent (SGD) or its variants (like Adam).

#### 3. Neural Network Architecture

The policy and target networks used in the DQN controller of this study are both feed-forward neural networks. The input layer dimension corresponds to the state space defined in **Section 3.4.3**, and the output layer dimension corresponds to the action space defined in **Section 3.4.4**. The network includes two hidden layers and uses ReLU as the activation function, with its specific architecture further defined in **Section 3.5.3**.

---
**【圖表建議：圖 3.4.1 - DQN 訓練與決策流程圖】**

建議在此處繪製一張圖，清晰地展示 DQN 的完整運作流程。圖中應包含以下兩個並行的循環：
1.  **決策循環 (Agent-Environment Interaction)**:
    *   從環境接收狀態 $s_t$。
    *   策略網路 $Q(s, a; \theta)$ 接收 $s_t$ 並輸出所有動作的 Q 值。
    *   使用 $\epsilon$-greedy 策略選擇動作 $a_t$。
    *   在環境中執行 $a_t$，獲得獎勵 $r_t$ 和新狀態 $s_{t+1}$。
    *   將轉換樣本 $(s_t, a_t, r_t, s_{t+1})$ 存入經驗回放記憶體 $\mathcal{D}$。
2.  **訓練循環 (Network Update)**:
    *   從 $\mathcal{D}$ 中隨機採樣一批轉換樣本。
    *   使用目標網路 $Q(s, a; \theta^-)$ 計算 TD 目標。
    *   計算策略網路 $Q(s, a; \theta)$ 的損失函數。
    *   執行梯度下降以更新策略網路的權重 $\theta$。
    *   定期將策略網路的權重複製到目標網路 ($\theta^- \leftarrow \theta$)。 

### 3.4.2 Neuroevolution Reinforcement Learning (NERL) Controller Design

Neuroevolution Reinforcement Learning (NERL) is the core innovative method proposed in this study. This approach combines the global search capabilities of evolutionary algorithms (EAs) with the non-linear function approximation power of neural networks. It aims to overcome challenges faced by traditional gradient-based DRL methods (like DQN) when dealing with sparse rewards and complex parameter spaces, such as unstable convergence or getting trapped in local optima.

Unlike DQN, which seeks to approximate a value function, neuroevolution's goal is to directly optimize in the **parameter space** of the policy. In the NERL framework, the weights and biases $\theta$ of a neural network controller (i.e., a policy $\pi_\theta$) are treated as an individual's **genotype**. The algorithm searches directly for the optimal policy parameters $\theta^*$ by applying evolutionary operations to a **population** of many individuals.

#### 1. Evolutionary Process

The core process of NERL revolves around an "evaluate → select → reproduce" evolutionary cycle, which iterates to improve the overall performance of the population. Assume at generation $g$, there is a population $P_g = \{\theta_1, \theta_2, ..., \theta_N\}$ containing $N$ individuals.

1.  **Evaluation**: Each individual $\theta_i$ in the population is deployed into an independent instance of the simulation environment to perform a full evaluation episode. During this episode, the policy $\pi_{\theta_i}$ makes all decisions independently. After the episode concludes, a **fitness score** $F(\theta_i)$ is calculated for the individual based on the system's macroscopic performance metrics (i.e., the global reward $R_{\text{global}}$ defined in **Section 3.4.5**). This process is highly parallelizable, which can significantly reduce training time.

2.  **Selection**: Based on the calculated fitness scores of all individuals, the algorithm selects high-performing individuals from the current population $P_g$ to serve as **parents** for generating the next generation. This study employs **Tournament Selection**, a mechanism that strikes a good balance between selection pressure and maintaining population diversity.

3.  **Reproduction**: A new offspring population $P_{g+1}$ is generated by applying genetic operations to the parents. The main operations include:
    *   **Elitism**: To prevent the loss of the best solutions found during evolution, the top $k$ elite individuals with the highest fitness in each generation are directly and completely copied to the next generation's population.
    *   **Crossover**: Simulating biological reproduction, two parent individuals $\theta_a$ and $\theta_b$ are selected, and their parameter vectors are mixed to create new offspring. This study uses **Uniform Crossover**.
    *   **Mutation**: After crossover, a small random perturbation is applied to the parameters of the offspring individuals. This operation is key to maintaining population diversity and avoiding premature convergence. This study uses **Gaussian Mutation**.

By iteratively executing the above cycle, the average fitness of the population steadily increases, eventually converging to a high-performance policy network capable of efficiently solving complex traffic control problems.

#### 2. Neural Network Architecture and Parameters

To ensure a fair and consistent comparison with the DQN baseline, the NERL controller uses the exact same neural network architecture as DQN. Its evolutionary process is governed by a series of key hyperparameters (such as population size, mutation rate, and elite retention ratio), the specific values of which for this experiment are detailed in the experimental configuration in **Section 3.5.3**.

---
**【圖表建議：圖 3.4.1 - NERL 演化循環示意圖】**

建議在此處繪製一張循環圖，說明 NERL 的核心運作流程。圖中應包含：
1.  **初始族群 $P_g$**: 展示多個神經網路個體 $\theta_i$。
2.  **並行評估**: 每個 $\theta_i$ 在獨立環境中運行，並計算其適應度 $F(\theta_i)$。
3.  **選擇**: 根據適應度分數，通過錦標賽選擇出父代。
4.  **繁殖生成 $P_{g+1}$**: 展示精英保留、交叉和變異操作，生成新一代族群。
5.  箭頭應清晰地指向下一個階段，形成一個從 $P_g$ 到 $P_{g+1}$ 的完整演化閉環。

### 3.4.3 State Space Design

The definition of the state space is a cornerstone of successful reinforcement learning. It must provide the agent with sufficient and meaningful information to make effective decisions, while also avoiding the "Curse of Dimensionality" caused by excessively high dimensions. In the RMFS traffic control problem of this study, the state $s_t$ of any intersection at decision time $t$ is defined as a feature vector that comprehensively reflects its local traffic conditions and considers the potential impact of neighboring and downstream intersections.

Specifically, $s_t$ is a **17-dimensional continuous vector**, composed as follows:

**1. Local State - 8 dimensions**: Describes the real-time traffic information of the intersection where the controller is located.
    *   **Horizontal Direction**:
        *   $s_t[0]$: **Queue Length** - The number of robots waiting to pass the intersection on the horizontal aisle.
        *   $s_t[1]$: **First Vehicle Waiting Time** - If the queue is not empty, this is the time the first robot in the queue has been waiting; otherwise, it is 0.
        *   $s_t[2]$: **Average Waiting Time** - The average waiting time of all waiting robots in the horizontal direction.
        *   $s_t[3]$: **Downstream Saturation** - The queue length of the next intersection in the horizontal direction, used to predict the potential risk of spillback.
    *   **Vertical Direction**:
        *   $s_t[4]$ - $s_t[7]$: The corresponding four features for the vertical aisle.

**2. Neighbor State - 8 dimensions**: Describes key information from the four neighboring intersections directly connected to the current one, helping the agent understand the broader traffic situation.
    *   **Each of the top, bottom, left, and right neighbors** includes 2 dimensions of information:
        *   $s_t[8], s_t[9]$: **Top Neighbor** - Vertical queue length, horizontal queue length.
        *   $s_t[10], s_t[11]$: **Bottom Neighbor** - Vertical queue length, horizontal queue length.
        *   $s_t[12], s_t[13]$: **Left Neighbor** - Vertical queue length, horizontal queue length.
        *   $s_t[14], s_t[15]$: **Right Neighbor** - Vertical queue length, horizontal queue length.

**3. Global State - 1 dimension**: Introduces a macroscopic indicator to help the agent align local decisions with overall system goals.
    *   $s_t[16]$: **Average Picking Station Queue** - The average queue length at the entrance of all picking stations. This is a critical system-level indicator, as picking stations are the final bottleneck for the entire material flow.

#### State Normalization

Since the 17 features described above have different physical units and numerical ranges (e.g., counts, time, ratios), feeding them directly into a neural network would cause features of different scales to have varying impacts on the gradient, leading to an unstable training process. Therefore, before feeding the state vector $s_t$ into the DRL model, this study employs an **Adaptive Normalization** technique. This technique dynamically tracks the running mean and standard deviation of each state feature during training and uses them to standardize the feature values to a distribution with a mean close to 0 and a standard deviation close to 1, thereby ensuring the stability and efficiency of model training.

### 3.4.4 Action Space Design

In contrast to the high-dimensional state space, this study designs a concise and intuitive discrete action space $\mathcal{A}$ for the DRL agent. At each decision point, the controller can select one action $a_t \in \mathcal{A}$ from a set of **6 discrete actions**. These actions not only cover basic traffic signal phase control but also introduce the ability to dynamically adjust local speed limits for more refined traffic flow management.

The action set $\mathcal{A}$ is defined as $\{0, 1, 2, 3, 4, 5\}$, where each integer corresponds to a specific control command:

#### 1. Basic Phase Control

This part of the actions is primarily responsible for managing the right-of-way at the intersection.

*   **Action 0 (`KEEP_CURRENT_PHASE`)**: **Maintain Current Phase**. This action keeps the current signal state of the intersection unchanged. This is the optimal choice when the existing traffic flow is smooth, or the cost of switching phases is higher than the potential benefit.
*   **Action 1 (`SWITCH_TO_VERTICAL_GREEN`)**: **Switch to Vertical Green**. This action forces the signal phase to a vertical green light and a horizontal red light, aiming to alleviate traffic pressure in the vertical direction.
*   **Action 2 (`SWITCH_TO_HORIZONTAL_GREEN`)**: **Switch to Horizontal Green**. This action forces the signal phase to a horizontal green light and a vertical red light, aiming to alleviate traffic pressure in the horizontal direction.

#### 2. Dynamic Speed Control

To more proactively manage traffic flow and prevent cascading spillbacks at bottleneck intersections, the model can also execute the following actions to dynamically adjust the speed limit of robots leaving the intersection. These actions do not change the signal phase themselves.

*   **Action 3 (`SET_SPEED_NORMAL`)**: **Set Speed to Normal**. This restores the speed limit for robots departing from this intersection to the default value (1.0), typically used after traffic conditions have eased.
*   **Action 4 (`SET_SPEED_SLOW`)**: **Set Speed to Slow**. This reduces the speed limit to a slow speed (0.5), used to proactively smooth traffic fluctuations when downstream congestion is anticipated.
*   **Action 5 (`SET_SPEED_VERY_SLOW`)**: **Set Speed to Very Slow**. This reduces the speed limit to a very slow speed (0.2), used to minimize the flow into a congested area when severe downstream congestion has already occurred.

#### Decision Interval

All DRL controllers operate at a fixed decision interval of $T_{\text{decision}} = 10$ ticks. This means the controller evaluates and selects a new action $a_t$ based on the current state $s_t$ every 10 simulation time steps. During this interval, the intersection will maintain the signal phase and speed limit set by the previous decision.

### 3.4.5 Reward Function Design

The reward function is the core mechanism in reinforcement learning that guides the agent's behavior. It translates the desired system objectives into an observable and quantifiable scalar feedback signal. To explore the effects of learning at different time scales, this study designed two distinct reward schemes: "Step Reward" and "Global Reward."

#### 1. Step Reward

The step reward scheme is designed to provide the agent with a dense, immediate, and local feedback signal. At the end of each decision interval ($T_{\text{interval}} = 10$ ticks), the system independently evaluates the local performance of each intersection and calculates a composite reward value. This high-frequency feedback helps the agent quickly learn basic traffic control heuristics, such as prioritizing high-priority tasks and reducing waiting vehicles.

For a single intersection $i$, its step reward $R_{\text{step}}(i)$ within a decision interval is composed of the following weighted components:

$$
R_{\text{step}}(i) = (R_{\text{flow}} - C_{\text{wait}} - C_{\text{switch}}) \times w_{\text{critical}}(i) \quad (3-19)
$$

where the components are defined as follows:

-   **Flow Reward ($R_{\text{flow}}$)**: A positive reward given based on the number of robots that successfully pass through the intersection and their task priorities.
    $$
    R_{\text{flow}} = \sum_{r \in P_i} w_{\text{pass}}(p(r)) \quad (3-20)
    $$
    Here, $P_i$ is the set of robots that passed through intersection $i$ during the decision interval, $p(r)$ is the task priority of robot $r$ (high, medium, low), and $w_{\text{pass}}$ is the corresponding priority reward weight.

-   **Waiting Cost ($C_{\text{wait}}$)**: A penalty imposed on robots still waiting in the queue at the intersection, based on their accumulated waiting time and task priority.
    $$
    C_{\text{wait}} = \sum_{r \in Q_i} w_{\text{wait}}(p(r)) \cdot t_{\text{wait}}(r) \quad (3-21)
    $$
    Here, $Q_i$ is the set of robots still waiting at intersection $i$, $t_{\text{wait}}(r)$ is the waiting time of robot $r$ (in ticks), and $w_{\text{wait}}$ is the corresponding priority penalty weight.

-   **Phase Switch Cost ($C_{\text{switch}}$)**: A fixed penalty for each signal phase switch to discourage excessively frequent and ineffective switching and to encourage the controller to maintain the continuity of traffic flow.
    $$
    C_{\text{switch}} = w_{\text{switch}} \cdot \mathbb{I}(\text{switched}) \quad (3-22)
    $$
    where $\mathbb{I}(\text{switched})$ is an indicator function that is 1 if a phase switch occurred and 0 otherwise. $w_{\text{switch}}$ is a fixed penalty weight.

-   **Critical Intersection Weighting ($w_{\text{critical}}(i)$)**: To make the agent prioritize learning to manage traffic near bottleneck areas like picking stations, the reward value for an intersection $i$ marked as "critical" is multiplied by an amplification factor greater than 1.

#### 2. Global Reward

The global reward scheme provides a sparse and delayed feedback signal, designed to guide the agent to learn complex strategies that are beneficial to the system's long-term, macroscopic goals. In this mode, the agent receives no immediate feedback throughout the entire evaluation episode ($T_{\text{episode}}$) and only calculates a single reward value at the end of the episode based on the final overall performance of the system.

To avoid the reward signal being dominated by a single metric due to direct addition/subtraction of indicators with different scales, this study designed a global reward function based on an efficiency ratio. This function uses the system's "output" as the numerator and the system's "cost" as the denominator. Its formula is defined as:

$$
R_{\text{global}} = \frac{N_{\text{completed}} \cdot w_{\text{completion}}}{\frac{E_{\text{total}}}{S_{\text{energy}}} + T_{\text{episode}} \cdot w_{\text{time}} + P_{\text{spillback}} + \epsilon} \quad (3-23)
$$

where the symbols are defined as follows:

-   $N_{\text{completed}}$: Total number of completed orders in the evaluation episode.
-   $w_{\text{completion}}$: Order completion reward weight.
-   $E_{\text{total}}$: Total energy consumption of the system during the episode (in EU), as detailed in Section 3.2.5.
-   $S_{\text{energy}}$: Energy scaling factor, used to adjust the energy cost to a comparable scale with the time cost.
-   $T_{\text{episode}}$: Total duration of the evaluation episode (in ticks).
-   $w_{\text{time}}$: Time penalty weight per tick.
-   $P_{\text{spillback}}$: A large penalty applied if severe spillback occurs at a picking station.
-   $\epsilon$: A very small positive constant (e.g., $10^{-6}$) to avoid division by zero.

This ratio-based design encourages the agent to pursue a high volume of completed orders while simultaneously considering energy and time efficiency, thereby learning a more balanced and sustainable operational strategy.

## 3.5 Experiment Design and Evaluation Method

To objectively and quantitatively answer the core question of this research—whether our proposed deep reinforcement learning traffic control strategy offers a significant advantage over traditional methods in improving warehouse system operational efficiency—this section details the overall experimental design, model training process, performance evaluation framework, and statistical analysis methods for the results.

A rigorous experimental design is the cornerstone for ensuring the reliability of the research conclusions. To this end, we will establish a comparative experimental matrix covering various control strategies and test them under a unified simulation environment and system load. All experiments will follow standardized training and evaluation procedures to eliminate the interference of irrelevant variables, ensuring that comparisons between different algorithms are fair and meaningful.

The structure of this section is as follows:
- **3.5.1 Experiment Design and Group Definition**: Defines all controller types (experimental groups) included in the experiment and describes the hardware and software environment configurations used for training.
- **3.5.2 Model Training Process**: Details the specific training steps for the DRL models (DQN and NERL) to ensure the reproducibility of the experiments.
- **3.5.3 DRL Model Hyperparameter Settings**: Details the hyperparameter settings used for the DRL models.
- **3.5.4 Evaluation Method and Comparison Framework**: Explains the standardized procedure for final performance evaluation after model training is complete, and the unified framework for comparing all experimental groups.

### 3.5.1 Experiment Design and Group Definition

To systematically evaluate the performance of different traffic control strategies, this study designed a comparative experiment consisting of twelve independent experimental groups. This design aims to comprehensively compare the performance of the two deep reinforcement learning methods proposed in this study (DQN and NERL), under different reward schemes and hyperparameter configurations, against two heuristic baseline controllers.

#### Experimental Group Definition

All experimental groups are run in the standardized warehouse simulation environment described in **Section 3.2.1**. The only variable is the traffic controller used at the intersections and its specific configuration. The detailed definitions of each experimental group are shown in the table below.

**Table 3.5.1: Experimental Group Definitions and Descriptions**

| Group | Controller Type | Reward Scheme | NERL Variant | NERL Eval. Ticks | Category | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| L | `TimeBased` | - | - | - | Baseline | Static controller with a fixed time cycle |
| K | `QueueBased` | - | - | - | Baseline | Dynamic reactive controller based on real-time queue length |
| J | `DQN` | `step` | - | - | DRL | DQN trained with step rewards (see Sec 3.5.3 for params) |
| I | `DQN` | `global` | - | - | DRL | DQN trained with global rewards (see Sec 3.5.3 for params) |
| A | `NERL` | `step` | **A (Exploratory)** | 3,000 | DRL | High mutation rate, short evaluation duration (see Sec 3.5.3) |
| C | `NERL` | `global` | **A (Exploratory)** | 3,000 | DRL | High mutation rate, short evaluation duration (see Sec 3.5.3) |
| B | `NERL` | `step` | **B (Exploitative)** | 3,000 | DRL | Low mutation rate, short evaluation duration (see Sec 3.5.3) |
| D | `NERL` | `global` | **B (Exploitative)** | 3,000 | DRL | Low mutation rate, short evaluation duration (see Sec 3.5.3) |
| E | `NERL` | `step` | **A (Exploratory)** | 8,000 | DRL | High mutation rate, long evaluation duration (see Sec 3.5.3) |
| G | `NERL` | `global` | **A (Exploratory)** | 8,000 | DRL | High mutation rate, long evaluation duration (see Sec 3.5.3) |
| F | `NERL` | `step` | **B (Exploitative)** | 8,000 | DRL | Low mutation rate, long evaluation duration (see Sec 3.5.3) |
| H | `NERL` | `global` | **B (Exploitative)** | 8,000 | DRL | Low mutation rate, long evaluation duration (see Sec 3.5.3) |

#### NERL Variant Parameter Details

To investigate the impact of the balance between "Exploration" and "Exploitation" during the evolutionary process on the final policy performance, this study designed two NERL variants with different evolutionary hyperparameters. The core difference lies in the mutation operation settings:

- **Variant A (Exploratory)**: This configuration aims to promote a broad search in the parameter space. It features a higher mutation rate (`mutation_rate = 0.3`) and a larger mutation strength (`mutation_strength = 0.2`). This allows offspring individuals a greater potential to jump out of the neighborhood of existing solutions and discover entirely new, potentially better strategies, but it may also risk slower convergence.

- **Variant B (Exploitative)**: This configuration focuses on fine-tuning the better solutions that have already been discovered. It uses a lower mutation rate (`mutation_rate = 0.1`) and a smaller mutation strength (`mutation_strength = 0.05`). This conservative mutation strategy helps with the stable convergence of the policy but may also increase the risk of getting stuck in a local optimum.

Furthermore, to study the effect of the sufficiency of individual policy evaluation on learning outcomes, each NERL variant will be trained and evaluated under two evaluation durations: `3,000` ticks and `8,000` ticks.

#### Hardware and Software Configuration

To ensure the consistency and reproducibility of the experimental results, all experiments were conducted in a standardized environment. Detailed hardware and software information has been provided in **Section 3.2.3**.

### 3.5.2 Model Training Process

To ensure that the DRL models can fully learn and converge to a satisfactory policy, and to guarantee fairness in comparisons between different models, this study designed a standardized model training process. This process details every step from model initialization to final model saving.

#### 1. DQN Training Process (for Groups I, J)

DQN training is an online, continuous learning process. A single complete DQN training experiment follows these steps:

1.  **Initialization**:
    a. Create a `DQNController` instance according to the hyperparameters defined in `Section 3.5.3` and the reward scheme (`step` or `global`) specified by the experimental group.
    b. Create an instance of the `Warehouse` simulation environment.

2.  **Training Loop**:
    a. Start a simulation lasting `N = 550,000` time steps (ticks).
    b. At each time step `t`, the `IntersectionManager` iterates through all intersections.
    c. For each intersection `i`:
        i.   The controller gets the current state `s_t` from the environment.
        ii.  An action `a_t` is selected using the policy network and an ε-greedy strategy.
        iii. Execute action `a_t`. The environment transitions to the next state `s_{t+1}`, and the immediate reward `r_t` is calculated by a `UnifiedRewardSystem` (this reward is 0 in `global` mode).
        iv.  The experience tuple `(s_t, a_t, r_t, s_{t+1})` is stored in the experience replay memory.
    d. **Experience Replay**: Every `k=32` time steps, a batch of experiences is randomly sampled from memory for learning.
    e. **Target Network Update**: Every `M=1,000` time steps, the weights of the policy network are copied to the target network.

3.  **Model Saving**: After the training is fully completed, the final policy network weights are saved as the final model.

#### 2. NERL Training Process (for Groups A-H)

NERL training is a generation-iterative, off-policy learning process. Its core procedure is uniform for all NERL groups but uses different hyperparameters depending on the specific group's configuration.

1.  **Initialization**:
    a. Create a `NEController` instance according to `Section 3.5.3` and the **specific experimental group** (A-H) definition. This step determines the following key hyperparameters:
        - **Reward Scheme**: `step` or `global`.
        - **Mutation Variant**: **A (Exploratory)** or **B (Exploitative)**, which determines the values of `mutation_rate` and `mutation_strength`.
        - **Evaluation Ticks**: `3,000` or `8,000`.
    b. The controller randomly initializes a population of `20` network individuals.

2.  **Evolutionary Loop**:
    a. Start an evolution process lasting `G = 30` generations.
    b. In each generation `g`:
        i.   **Parallel Evaluation**: For the `20` individuals in the population, `20` independent and parallel simulation environments are launched.
        ii.  Each individual `j` runs a full evaluation episode in its dedicated environment. The duration of the episode is determined by the `eval_ticks` parameter of its experimental group (`3,000` or `8,000` ticks).
        iii. After the episode ends, the `UnifiedRewardSystem` calculates the fitness score `f_j` for individual `j` based on the reward scheme (`step` or `global`) specified for its group.
        iv.  **Evolutionary Operations**: Once the fitness scores for all individuals are calculated, the controller performs a full evolutionary operation (selection, crossover, mutation) based on the group's mutation variant (`A` or `B`) to generate a new offspring population.
        v.   The new offspring population becomes the starting population for the next generation, `g+1`.

3.  **Model Saving**:
    a. At the end of each generation, the algorithm saves the individual with the highest fitness in that generation as the contemporary best model.
    b. After all `30` generations are complete, the model with the historically highest fitness score among all generations' best models is selected and saved as the final model for that experimental group.

### 3.5.3 DRL Model Hyperparameter Settings

To ensure the reproducibility and validity of the DRL experiments in this study, this section details the key hyperparameters used in training the `DQN` and `NERL` controllers. These parameters were set based on preliminary convergence and stability experiments and remained fixed during the formal training period.

#### 1. Common Neural Network Architecture

To ensure a fair comparison between the baseline (DQN) and the core method (NERL), both adopted the exact same neural network architecture. This architecture strikes a balance between the model's expressive power and computational efficiency, and is sufficient to handle the traffic control problem in this study.

| Layer | Type | Input Dim | Output Dim | Activation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Input | 17 | 17 | - |
| 2 | Fully Connected (FC 1) | 17 | 128 | ReLU |
| 3 | Fully Connected (FC 2) | 128 | 64 | ReLU |
| 4 | Output | 64 | 6 | - |


#### 2. DQN-Specific Hyperparameters

The following table lists the main hyperparameters used during the training of the `DQN` controller (experimental groups J, I).

| Hyperparameter | Code Variable | Value | Description |
| :--- | :--- | :--- | :--- |
| Learning Rate | `learning_rate` | 5e-4 | The learning rate for the Adam optimizer. |
| Gamma (Discount Factor) | `gamma` | 0.99 | The discount factor for future rewards. A value closer to 1 indicates a greater emphasis on long-term returns. |
| Initial Epsilon | `epsilon` | 1.0 | The initial probability of choosing a random action at the beginning of training. |
| Minimum Epsilon | `epsilon_min` | 0.01 | The lower bound for epsilon decay. |
| Epsilon Decay Rate | `epsilon_decay` | 0.9995 | The exponential decay factor by which epsilon is multiplied after each training step. |
| Experience Replay Memory Size| `memory_size` | 50,000 | The maximum number of $(s, a, r, s')$ transition samples to store. |
| Batch Size | `batch_size` | 8,192 | The number of samples to draw from memory for each network update. |
| Target Network Update Freq | `target_update_freq` | 1,000 | The frequency (in training **steps**) at which the policy network's weights are copied to the target network. |

#### 3. NERL-Specific Hyperparameters

The following table lists the main hyperparameters used during the evolution of the `NERL` controller (experimental groups A-H). The mutation rate and mutation strength vary according to the **Exploratory (A)** and **Exploitative (B)** variants defined in **Section 3.5.1**.

| Hyperparameter | Code Variable | Variant A (Exploratory) | Variant B (Exploitative) | Description |
| :--- | :--- | :--- | :--- | :--- |
| Population Size | `population_size` | 20 | 20 | The number of individuals (neural networks) in each generation. |
| Elite Ratio | `elite_ratio` | 0.2 | 0.2 | The proportion of the highest-fitness individuals directly preserved in each generation. |
| Tournament Size | `tournament_size` | 4 | 4 | The number of individuals randomly compared in each tournament selection. |
| Crossover Rate | `crossover_rate` | 0.8 | 0.8 | The probability of two parent individuals undergoing genetic crossover. |
| Mutation Rate | `mutation_rate` | **0.2** | **0.1** | The base probability of an individual's genes (network weights) mutating. |
| Mutation Strength | `mutation_strength` | **0.15** | **0.15** | The standard deviation for Gaussian mutation, controlling the magnitude of mutation. |
| Evaluation Ticks | `eval_ticks` | 3000 / 8000 | 3000 / 8000 | The duration (in ticks) for evaluating each individual. |

These hyperparameters collectively define the learning behaviors of the two DRL methods and form an important basis for the subsequent experimental analysis and results comparison.

### 3.5.4 Evaluation Method and Comparison Framework

After the DRL models are trained according to the process described in `Section 3.5.2`, a standardized evaluation procedure is designed to ensure all controllers are compared on a fair and unbiased basis. This procedure aims to simulate a fixed, repeatable "test day" scenario and to quantify the performance of each control strategy using a predefined set of Key Performance Indicators (KPIs).

#### 1. Standardized Evaluation Process

For each experimental group defined in `Section 3.5.1` (including the two baseline controllers and all trained DRL controllers), the following standardized evaluation procedure will be executed:

1.  **Model Loading**: For the DRL experimental groups, load their corresponding final trained models and set them to pure **Inference Mode**. In this mode, DQN's ε-greedy exploration will be turned off (ε=0), and NERL will consistently use its historically best-performing individual for decision-making.
2.  **Environment Reset**: Initialize a simulation environment that is identical to the one used for training but uses a set of **fixed random seeds that were never used in training**. This ensures that all controllers face the exact same initial conditions, order sequences, and random events, thus eliminating interference from randomness.
3.  **Execution of Evaluation**: Run a complete simulation of a fixed duration (e.g., `T_{eval} = 50,000` ticks) in the standardized environment.
4.  **Data Logging**: During the simulation, a `PerformanceReportGenerator` will record time-series data of all key performance indicators at fixed intervals (e.g., every 10 ticks).
5.  **Repeated Execution**: To eliminate the impact of extreme random events in a single run and to obtain more statistically significant results, the above steps 2-4 will be **repeated 3 times** for each experimental group. Each run will use a different, but shared across groups, set of random seeds. The final performance will be the average of these 3 runs.

#### 2. Performance Comparison Framework

After the 3 repeated evaluation runs are completed, the data for each experimental group will be aggregated and compared. The comparison framework will revolve around the Key Performance Indicators defined in `Section 3.2.4`, which can be categorized into three main types:

**A. Core Efficiency Indicators**
These indicators directly reflect the system efficiency that is of primary concern to this study.
- **Total Energy Consumption**: Evaluates the system's energy usage efficiency. Lower is better.
- **Completed Orders Count**: Measures the total output of the system within a fixed time. Higher is better.

**B. Process Quality Indicators**
These indicators indirectly reflect the smoothness and service quality of the system's operation.
- **Average Order Processing Time**: Measures the system's response speed. Lower is better.
- **Average Intersection Waiting Time**: Directly measures the effectiveness of the traffic control strategy. Lower is better.
- **Total Stop-and-Go Count**: Reflects the smoothness of the traffic flow. Lower is better.

Finally, the average KPI data for all experimental groups will be compiled into a comprehensive performance comparison table for in-depth analysis and discussion in the next chapter. Additionally, the collected time-series data will be plotted to visually demonstrate the dynamic behavior differences between the various strategies during the simulation. 