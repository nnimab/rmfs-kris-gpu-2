# 1.1 Research Background and Motivation

The global retail industry is undergoing a structural transformation driven by e-commerce. Projections indicate that the annual value of global retail e-commerce will grow to 6.42 trillion USD by 2025, accounting for over 20% of total retail sales [1]. To cope with the new normal of e-commerce orders, characterized by "small batches, high frequency, and time sensitivity," traditional warehousing models are no longer adequate. This has prompted businesses to adopt **Robotic Mobile Fulfillment Systems (RMFS)** on a large scale. In an RMFS, hundreds of Autonomous Mobile Robots (AMRs) operate collaboratively within a grid-based warehouse, capable of increasing picking efficiency by several folds.

However, the high density of AMR operations also creates new operational bottlenecks. **Traffic congestion at intersections, waiting delays between robots, and frequent acceleration/deceleration behaviors** not only directly limit the system's overall throughput but also significantly increase energy consumption and carbon emissions. This issue has become critically important under the increasingly stringent global sustainability and carbon neutrality policies:

*   **Significant Carbon Footprint**: Carbon emissions from transportation and warehousing activities account for approximately 24% of total global greenhouse gas emissions and have been identified as a priority area for carbon reduction by international logistics leaders like DHL [2].
*   **Urgent Policy Pressure**: The European Union's **Carbon Border Adjustment Mechanism (CBAM)** was initiated in 2023 and is expected to be fully implemented by 2026. This mechanism will impose additional costs on high-carbon-intensity imported products, compelling companies throughout the supply chain to rigorously scrutinize and manage carbon emissions in their warehousing and transportation links [3].

Against this backdrop, academia has begun to apply intelligent methods such as Reinforcement Learning (RL) to optimize RMFS operations. Some studies have used deep reinforcement learning to schedule orders to minimize costs [4], or adjusted traffic strategies and robot speeds to reduce total energy consumption by about 3–5% [5]. However, these studies either focus on order-level scheduling or still have room for exploration in the trade-off between energy consumption and efficiency. More specifically, **there is currently a lack of a control framework that focuses on the intersection level, aiming to achieve the dual optimization goals of "energy-efficiency" at a microscopic level by reducing unnecessary waiting and frequent "stop-and-go" behaviors.**

To fill this research gap, this study employs **Neuroevolution Reinforcement Learning (NERL)** techniques to design an intersection controller. This method combines the global search capabilities of evolutionary algorithms with the real-time decision-making advantages of deep reinforcement learning. It aims to provide an "adaptive, energy-aware" right-of-way allocation mechanism for RMFS intersections, with the expectation of effectively reducing the unit task energy consumption of AMRs while maintaining order processing efficiency.

# 1.2 Research Objectives

To validate the aforementioned concept and answer the core research questions, this study formulates the following four specific objectives, the results of which will be detailed in subsequent chapters:

1.  **Construct a High-Fidelity RMFS Simulation and Control Platform**
    *   Establish a physical warehouse environment including a central storage area, one-way aisles, workstations, and charging stations.
    *   Design a modular traffic control system architecture based on the Strategy and Factory patterns to support the flexible integration and fair comparison of different algorithms (see Section 3.2 for details).

2.  **Design and Implement Multiple Traffic Control Strategies**
    *   Develop two heuristic baseline controllers: a **Time-Based Controller** based on fixed time cycles, and a **Queue-Based Controller** based on real-time waiting queues (see Section 3.3 for details).
    *   Implement a value-based deep reinforcement learning method, the **Deep Q-Network (DQN)**, as a DRL benchmark (see Section 3.4.1 for details).
    *   Develop the core contribution of this study, the **Neuroevolution Reinforcement Learning (NERL) Controller**, and investigate the impact of different evolutionary hyperparameters (exploratory vs. exploitative) (see Section 3.4.2 for details).

3.  **Design and Execute Rigorous Controlled Experiments**
    *   Define a comprehensive set of performance evaluation metrics covering efficiency, throughput, and stability (see Section 3.2.4 for details).
    *   Design a comparison matrix of thirteen independent experimental groups to systematically compare the performance of different controllers under two reward modes (step vs. global) and different evaluation durations (see Section 3.5.1 for details).

4.  **Quantitative Analysis and Comparison**
    *   Conduct in-depth quantitative analysis and comparison of the performance of all control strategies based on experimental data.
    *   Systematically evaluate the performance of different controllers on the two core dimensions of "throughput efficiency" and "energy efficiency," and conduct an in-depth discussion of their strategy stability and trade-off characteristics (see Section 4.3 for details).

# 1.3 Research Scope and Limitations

To focus on the core problem and ensure the depth of the research, this study explicitly defines its scope. The following lists the core areas covered by this research and the parts not covered for model simplification.

## 1.3.1 Research Scope

| Item | Content | Description |
| :--- | :--- | :--- |
| **Core Problem** | Dynamic allocation of right-of-way at intersections. | The research focuses on solving the congestion and energy waste problems caused by improper intersection traffic coordination. |
| **Control Strategies** | Time-Based, Queue-Based, DQN, NERL. | Covers a comprehensive comparison from static rules, dynamic heuristics, to two different DRL frameworks. |
| **Optimization Goal** | Explore the trade-off relationship between "order completion rate" and "total energy consumption". | Adopts a multi-objective comparison perspective to evaluate the positioning and performance of different strategies on the efficiency-energy consumption trade-off spectrum. |
| **Evaluation Metrics** | Efficiency and throughput metrics as defined in Section 3.2.4. | Uses a complete set of quantitative metrics to comprehensively evaluate the pros and cons of each controller. |

## 1.3.2 Research Limitations

This study intentionally excludes the following issues from its scope to ensure focus on the core problem. These issues can serve as future research directions.

*   **Path Planning**: This study does not involve global path planning algorithms for robots from start to destination, assuming all robots follow a predefined shortest path.
*   **Slotting Assignment**: This study does not optimize the storage location of goods (SKUs) on pods or the storage location of pods in the warehouse, assuming they are randomly or pre-configured.
*   **Charging Strategy Management**: Although charging stations exist in the simulation environment, this study does not involve strategies for monitoring robot battery levels and proactively dispatching them for charging.
*   **Homogeneous Robots Assumption**: This study assumes all robot individuals have consistent performance, without considering individual differences caused by factors like hardware aging and wear in the real world.


# 3.2.1 Warehouse Simulation Environment Design

To effectively evaluate traffic control strategies, this study first constructs a high-fidelity warehouse simulation environment. This environment not only defines the physical layout but also includes various dynamic entities and their interaction rules, collectively forming a complex Robotic Mobile Fulfillment System (RMFS). This section will detail its design.

### 1. Physical Environment and Layout

The simulated warehouse is built on a two-dimensional discrete grid, where each grid cell has a specific function. The overall layout adopts a functional zoning design to ensure an orderly operational flow.

-   **Central Storage Area**: Located in the center of the warehouse, composed of a dense arrangement of **Pod Locations**. The aisles in this area are designed as strict **One-way Aisles**, with the flow directions of horizontal and vertical aisles alternating. This design physically simplifies the complexity of traffic management to a great extent, aiming to reduce potential conflicts when robots move in opposite directions.
-   **Workstation Area**: Distributed on both sides of the warehouse. One side consists of **Picking Stations**, which are the exits for order fulfillment; the other side has **Replenishment Stations**, which are the entry points for goods into the system.
-   **Charging Station**: Scattered within the storage area, converted from some pod locations, for robots to charge autonomously.

**[Figure Suggestion: Figure 3.2.1 - Warehouse Layout Diagram]**
To visually demonstrate the layout, it is recommended to insert a diagram here, using different colors to mark the storage area, picking area, replenishment area, and charging stations, and using arrows to clearly indicate the flow direction of the one-way aisles.

### 2. Core Entities and Lifecycles

The dynamic behavior of the system is driven by the interactions between several core entities.

-   **Robot**: As the most central active unit in the system, the robot has a complex state machine to manage its workflow, including states like `idle`, `taking_pod`, `delivering_pod`, `station_processing`, and `returning_pod`. This study establishes a detailed physical and energy model for the robot. Its energy consumption calculation not only considers the load but also includes startup costs and regenerative braking (brake energy recovery), providing a solid foundation for energy efficiency evaluation. In addition, the robot has priority-based autonomous obstacle avoidance logic, enabling it to resolve local conflicts to some extent.

**[Figure Suggestion: Figure 3.2.2 - Robot State Transition Diagram]**
To clearly show the robot's workflow, it is recommended to insert a UML state machine diagram here, depicting its core states and the events that trigger state transitions (e.g., "new task assigned," "arrived at workstation").

-   **Pod**: A mobile carrier for storing goods (SKUs). Each pod can store multiple types of SKUs and records the current quantity and replenishment threshold for each SKU. When the stock level falls below the threshold, the system automatically triggers a corresponding replenishment task.

-   **Station**: A node for human-robot collaboration. When a robot delivers a pod to a workstation, the system simulates the picking or replenishment delay of a worker. To handle high traffic, workstations are also designed with a dynamic path adjustment mechanism, activating a backup long path to alleviate congestion when there are too many robots in the station.

**[Figure Suggestion: Figure 3.2.3 - Warehouse Annotation Diagram]**
### 3. Dynamic Parameters and Load Settings

To ensure all experiments are conducted under a standardized and representative load pressure, this study unified the system's dynamic parameters.

-   **Number of Robots**: In all simulation experiments, **20** autonomous mobile robots are configured in the warehouse (`num_robot = 20` in `warehouse_generator.py`). This number is intended to create a medium-density traffic environment, sufficient to cause traffic congestion and resource competition, thereby effectively distinguishing the performance of different control strategies.
-   **Order Generation**: The system's load consists of two parts:
    - **Initial Backlog Orders**: At the start of the simulation, the system will first generate **50** backlog orders to simulate the pending tasks accumulated at the beginning of a workday in the real world.
    - **Dynamic Order Generation**: During the simulation, the system will dynamically generate new orders at a stable rate. According to the `config_orders` function in `warehouse_generator.py`, this rate is designed to provide a continuous and saturated task flow to the system, to avoid situations where an insufficient number of orders prevents a full evaluation of the controller's processing capacity under high load.

### 4. Order and Task Flow

The driving force of the simulation comes from orders. An **Order** represents a customer's request, containing multiple SKUs that need to be picked. The system breaks down an order into one or more **Jobs**. The core of a job is "transporting a specified pod to a specified workstation," which is the smallest work unit that can be directly assigned to a robot. The entire flow is as follows:
1.  The system receives an order.
2.  The SKUs required by the order are located on specific pods.
3.  The system generates one or more jobs and places them in the job queue.
4.  An idle robot takes a job from the queue and begins its work lifecycle of picking up, delivering, and returning.
5.  When all SKUs required for an order have been successfully delivered to the workstation, the order is marked as completed.

### 5. Intersection Design and Classification

In addition to the macroscopic layout, this study provides a clear classification and definition of the microscopic traffic nodes within the warehouse—the intersections. This is crucial for the subsequent controller design.

-   **Standard Intersection**: This is the basic unit that constitutes the main body of the warehouse traffic network, formed by the convergence of two mutually perpendicular one-way aisles. All intersections not specifically defined otherwise belong to this category.

-   **Critical Intersection**: Based on their strategic importance in the warehouse layout, a portion of intersections are marked as "critical intersections." These are traffic nodes on the entry or exit paths directly connected to **workstations (picking or replenishment stations)**. They are the mandatory paths for entering and exiting workstations and constitute the main traffic **bottlenecks** of the entire warehouse system. The management efficiency of these intersections will directly affect the throughput of workstations, the length of robot queues, and may trigger **spillback** congestion that spreads to the storage area. Therefore, in the design of the reinforcement learning reward function (see Section 3.4.5), these intersections will be given higher weights to guide the agent to prioritize learning their effective management.

**[Figure Suggestion: Figure 3.2.4 - Warehouse Intersection Classification and Critical Intersection Map]**
To visually display the geographical distribution of different intersections, it is recommended to insert a warehouse layout map here, consistent in style with Figure 3.2.1. In the map, different symbols or colors should be used to clearly mark the locations of standard intersections and all critical intersections, especially their adjacency to picking and replenishment stations.

# 3.2.4 Performance Evaluation Metric Definitions

To objectively and quantitatively evaluate the pros and cons of different traffic control strategies, this study establishes a comprehensive set of Key Performance Indicators (KPIs). To define them clearly, we first agree on the following mathematical notations:
- $R$: The set of all robots in the warehouse.
- $O_{\text{completed}}$: The set of all completed orders within the simulation period.
- $P$: The set of all robot passing events at intersections.
- $T_{\text{sim}}$: The total simulation duration, in units of $ticks$.

### 1. Efficiency Metrics

**Total Energy Consumption**
This metric measures the overall energy efficiency of the system and is one of the core optimization goals of this study. It is calculated as the sum of the energy consumed by all robot activities during the simulation (see Section 3.2.5 for the detailed calculation model).
$$
E_{\text{total}} = \sum_{r \in R} E_r
$$
where $E_r$ represents the total energy consumption of a single robot $r$ throughout the simulation, in energy units (EU). To gain a deeper understanding of the composition of total energy consumption, this study further defines two highly related **Diagnostic Metrics**, which are the direct microscopic behaviors leading to inefficient energy consumption:

-   **Total Stop-and-Go Count**: This metric reflects the smoothness of traffic flow. Each time a robot restarts from a stationary state, it incurs a significant additional energy cost (see `STARTUP_ENERGY_COST` in `robot.py`). Therefore, frequent starts and stops are an important component of total energy consumption. It is defined as the sum of all robot start-stop counts:
    $$
    S_{\text{total}} = \sum_{r \in R} N_{\text{s-g}}(r)
    $$
    where $N_{\text{s-g}}(r)$ represents the total number of start-stops for robot $r$.

-   **Average Intersection Waiting Time**: This metric directly reflects the coordination efficiency of the traffic control strategy. Longer waiting times not only reduce order processing efficiency but also mean that robots spend more time in idle or slow-moving states, indirectly increasing total energy consumption. It is calculated as the average waiting time for each robot passing event at an intersection:
    $$
    W_{\text{avg}} = \frac{1}{|P|} \sum_{p \in P} t_{\text{wait}}(p)
    $$
    where $|P|$ is the total number of times robots pass through intersections, and $t_{\text{wait}}(p)$ is the waiting time for a single passing event $p$.

### 2. Throughput Metrics

**Completed Orders Count**
This metric directly measures the total output of the system within a fixed time, reflecting the overall operational efficiency.
$$
N_{\text{orders}} = |O_{\text{completed}}|
$$

**Average Order Processing Time**
This metric measures the system's response speed in processing a single order. It is defined as the average time taken for all completed orders from the start of processing to the end.
$$
T_{\text{avg_order}} = \frac{1}{|O_{\text{completed}}|} \sum_{o \in O_{\text{completed}}} (t_{\text{complete}}(o) - t_{\text{start}}(o))
$$
where $t_{\text{complete}}(o)$ and $t_{\text{start}}(o)$ are the completion and start times of order $o$, respectively, both in units of $ticks$.

### 3. Stability Metrics

The stability in this study is primarily evaluated through the **Coefficient of Variation (CV)** of the main efficiency and throughput metrics across multiple independent runs. A lower CV value for a control strategy indicates more stable performance output and higher predictability.

# 3.4.5 Reward Function Design

The reward function is the core mechanism in reinforcement learning that guides the agent's behavior by translating the system's desired goals into an observable, quantifiable scalar feedback signal. To explore the learning effects at different time scales, this study designs two distinct reward modes: "Step Reward" and "Global Reward."

### 1. Step Reward

The step reward mode aims to provide the agent with a dense, immediate, and local feedback signal. At the end of each decision interval ($T_{\text{interval}} = 10$ ticks), the system independently evaluates the local performance of each intersection and calculates a composite reward value. This high-frequency feedback helps the agent quickly learn basic traffic control heuristics.

#### Basic Conceptual Model

The basic conceptual model of the step reward aims to maximize local traffic efficiency. For a single intersection $i$, its reward $R_{\text{step}}(i)$ is composed of the following weighted components:

$$
R_{\text{step}}(i) = (R_{\text{flow}} - C_{\text{wait}} - C_{\text{switch}}) \times w_{\text{critical}}(i)
$$

The definitions of each component are as follows:

-   **Flow Reward ($R_{\text{flow}}$)**: A positive reward given based on the number of robots that successfully pass the intersection and their task priorities.
-   **Waiting Cost ($C_{\text{wait}}$)**: A penalty imposed on robots still waiting in the intersection queue, based on their cumulative waiting time and task priority.
-   **Phase Switch Cost ($C_{\text{switch}}$)**: A fixed penalty for each change of the traffic light phase to encourage the controller to maintain traffic flow continuity.
-   **Critical Intersection Weighting ($w_{\text{critical}}(i)$)**: For "critical" intersections near bottleneck areas like picking stations, their reward value is amplified to guide the agent to prioritize learning to manage these important areas.

#### Enhanced Implementation Model

In subsequent research iterations, to better align the step reward with the system's energy efficiency goals, this study implemented an **enhanced step reward model** in the final simulator. This model, building upon the basic concept, introduces direct rewards for energy-saving behaviors. Its concept can be represented as:

$$
R_{\text{step_enhanced}}(i) = R_{\text{step}}(i) + B_{\text{energy}} + B_{\text{congestion}}
$$

The newly added reward terms are defined as follows:
-   **Energy Bonus ($B_{\text{energy}}$)**: This is a positive reward term aimed at encouraging the controller to make decisions that favor energy conservation. It consists of two sub-components:
    1.  **Low-Speed Passage Bonus**: A small reward is given when a robot is detected passing through the intersection at a smooth low speed (not maximum speed), to encourage constant-speed driving and avoid unnecessary sharp accelerations.
    2.  **Low-Energy Behavior Bonus**: A small reward is given when a robot's actual instantaneous energy consumption within a time unit is detected to be below a preset threshold (indicating the robot may have avoided a high-energy stop-and-go event).
-   **Congestion Management Bonus ($B_{\text{congestion}}$)**: When congestion is detected in a downstream critical area (such as the entrance to a picking station), a positive reward is given if the controller can make low-priority robots wait at an upstream intersection. This mechanism is designed to encourage the controller to learn "source traffic control" to avoid exacerbating downstream congestion.

This enhanced design allows controllers under the `Step` reward mode to possess certain tactical energy-saving and congestion management capabilities while primarily focusing on local traffic efficiency.

### 2. Global Reward

The global reward mode provides a sparse, delayed feedback signal aimed at guiding the agent to learn complex strategies that are beneficial to the system's long-term, macroscopic goals. In this mode, the agent receives no immediate feedback throughout the evaluation episode ($T_{\text{episode}}$), and a single reward value is calculated only at the end of the episode based on the final overall performance of the system.

To avoid the reward signal being dominated by a single metric due to direct addition/subtraction of metrics with different scales, this study designed a global reward function based on an efficiency ratio. This function takes the system's "output" as the numerator and the system's "cost" as the denominator. Its formula is defined as follows:

$$
R_{\text{global}} = \frac{N_{\text{completed}} \cdot w_{\text{completion}}}{\frac{E_{\text{total}}}{S_{\text{energy}}} + T_{\text{episode}} \cdot w_{\text{time}} + P_{\text{spillback}} + \epsilon}
$$

The symbols are defined as follows:

-   $N_{\text{completed}}$: Total number of orders completed during the evaluation episode (unit: count).
-   $w_{\text{completion}}$: Weight for the order completion reward.
-   $E_{\text{total}}$: Total energy consumption of the system during the episode (unit: EU), as defined in detail in Section 3.2.5.
-   $S_{\text{energy}}$: **Energy Scaling Factor**. This parameter is crucial. Its role is to balance the scales of energy cost ($E_{\text{total}}$) and time cost ($T_{\text{episode}}$) when calculating the total cost (denominator). Since the numerical value of total energy consumption is usually much larger than the total duration, the reward signal would be completely dominated by the energy cost without scaling. In this study's code implementation (`ai/unified_reward_system.py`), this value is set to **100.0** to ensure that energy and time costs have comparable influence in the reward calculation.
-   $T_{\text{episode}}$: Total duration of the evaluation episode (unit: ticks).
-   $w_{\text{time}}$: Time penalty weight per tick.
-   $P_{\text{spillback}}$: A large penalty applied if severe spillback occurs at a picking station.
-   $\epsilon$: A very small positive constant (e.g., $10^{-6}$) to avoid division by zero.

This ratio-based design encourages the agent to pursue a high number of completed orders while simultaneously considering energy and time efficiency, thereby learning a more balanced and sustainable operational strategy.

> **Note**: The specific weight values used in all reward functions, such as `completion_bonus`, `pass_high_priority`, and `switch_penalty`, are consolidated in **Table 3.5.2** in **Section 3.5.3**. This ensures that this section focuses on the design philosophy while maintaining the reproducibility of the research.

# 3.5.1 Experiment Design and Group Definitions

To systematically evaluate the performance of different traffic control strategies, this study designed a controlled experiment consisting of thirteen independent experimental groups. This design aims to comprehensively compare the performance of the Neuroevolution Reinforcement Learning (NERL) method proposed in this study, under different reward modes and hyperparameter configurations, against standard reinforcement learning (DQN) and three heuristic baseline controllers.

### Experimental Group Definitions

All experimental groups are run under the standardized warehouse simulation environment described in **Section 3.2.1**. The only variable is the traffic controller used at the intersections and its specific configuration. The detailed definitions of each experimental group are shown in the table below. To facilitate citation in the text and maintain clarity in charts, this study uses a hybrid naming convention with "Short Name" and "Full Name" correspondence.

**Table 3.5.1: Experimental Group Definitions and Descriptions**

| Short Name | Controller | Reward | NERL Variant | Eval Ticks | Category | Full Name |
| :--- | :--- | :--- | :--- | :--- | :--- |:--- |
| **`Baseline-T`** | `TimeBased` | - | - | - | Baseline | `time_based` |
| **`Baseline-Q`** | `QueueBased` | - | - | - | Baseline | `queue_based` |
| **`Baseline-N`** | `NoController` | - | - | - | Baseline | `no_controller` |
| **`DQN-S`** | `DQN` | `step` | - | - | DRL | `dqn_dqn_model_step_55000` |
| **`DQN-G`** | `DQN` | `global` | - | - | DRL | `dqn_dqn_model_global_55000` |
| **`NERL-S-A3`** | `NERL` | `step` | A (Exploratory) | 3,000 | DRL | `nerl_nerl_step_a3000ticks` |
| **`NERL-G-A3`** | `NERL` | `global` | A (Exploratory) | 3,000 | DRL | `nerl_nerl_global_a3000ticks` |
| **`NERL-S-B3`** | `NERL` | `step` | B (Exploitative) | 3,000 | DRL | `nerl_nerl_step_b3000ticks` |
| **`NERL-G-B3`** | `NERL` | `global` | B (Exploitative) | 3,000 | DRL | `nerl_nerl_global_b3000ticks` |
| **`NERL-S-A8`** | `NERL` | `step` | A (Exploratory) | 8,000 | DRL | `nerl_nerl_step_a8000ticks` |
| **`NERL-G-A8`** | `NERL` | `global` | A (Exploratory) | 8,000 | DRL | `nerl_nerl_global_a8000ticks` |
| **`NERL-S-B8`** | `NERL` | `step` | B (Exploitative) | 8,000 | DRL | `nerl_nerl_step_b8000ticks` |
| **`NERL-G-B8`** | `NERL` | `global` | B (Exploitative) | 8,000 | DRL | `nerl_nerl_global_b8000ticks` |

### Detailed NERL Variant Parameters

To investigate the impact of the balance between "Exploration" and "Exploitation" during the evolutionary process on the final policy performance, this study designed two NERL variants with different evolutionary hyperparameters. The core difference lies in the mutation operation settings:

- **Variant A (Exploratory)**: This configuration aims to promote a broad search in the parameter space. It is set with a higher mutation rate (`mutation_rate = 0.3`) and a larger mutation strength (`mutation_strength = 0.2`). This allows offspring individuals a greater potential to jump out of the neighborhood of existing solutions and discover entirely new, potentially better policies, but it may also risk slower convergence.

- **Variant B (Exploitative)**: This configuration focuses on fine-tuning the better solutions that have already been found. It uses a lower mutation rate (`mutation_rate = 0.1`) and a smaller mutation strength (`mutation_strength = 0.05`). This conservative mutation strategy helps with the stable convergence of the policy but also increases the risk of getting trapped in a local optimum.

Furthermore, to study the effect of the adequacy of individual policy evaluation on learning outcomes, each NERL variant will be trained and evaluated under two evaluation durations: `3,000` ticks and `8,000` ticks.

### Hardware and Software Configuration

To ensure the consistency and reproducibility of the experimental results, all experiments were conducted in a standardized environment. Detailed hardware and software information has been described in **Section 3.2.3**.

# 3.5.2 Model Training Process

To ensure that the DRL models can fully learn and converge to an optimal policy, and to guarantee a fair comparison between different models, this study designed a standardized model training process. This process details every step from model initialization to final model saving.

### 1. DQN Training Process (Corresponding to groups `DQN-S`, `DQN-G`)

The training of DQN is an online, continuous learning process. A single complete DQN training experiment follows this procedure:

1.  **Initialization**:
    a. Create a `DQNController` instance based on the hyperparameters defined in Section `3.4.4` and the reward mode (`step` or `global`) specified by the experimental group.
    b. Create an instance of the `Warehouse` simulation environment.

2.  **Training Loop**:
    a. Start a simulation that lasts for `N = 550,000` time steps (ticks).
    b. At each time step `t`, the `IntersectionManager` iterates through all intersections.
    c. For each intersection `i`:
        i.   The controller obtains the current state `s_t` from the environment.
        ii.  An action `a_t` is selected using the policy network and an ε-greedy strategy.
        iii. The action `a_t` is executed, the environment transitions to the next state `s_{t+1}`, and the immediate reward `r_t` is calculated by the `UnifiedRewardSystem` (this reward is 0 in `global` mode).
        iv.  The experience tuple `(s_t, a_t, r_t, s_{t+1})` is stored in the experience replay memory.
    d. **Experience Replay**: Every `k=32` time steps, a batch of experiences is randomly sampled from the memory for learning.
    e. **Target Network Update**: Every `M=1,000` time steps, the weights of the policy network are copied to the target network.

3.  **Model Saving**: After the training is fully completed, the final policy network weights are saved as the final model.

### 2. NERL Training Process (Corresponding to groups `NERL-S-A3` to `NERL-G-B8`)

The training of NERL is an off-policy, generation-iterative learning process. Its core process is uniform for all NERL groups but incorporates different hyperparameters based on the specific group's configuration.

1.  **Initialization**:
    a. Create a `NEController` instance based on Section `3.4.4` and the definition of the **specific experimental group**. This step determines the following key hyperparameters:
        - **Reward Mode**: `step` or `global`.
        - **Mutation Variant**: **A (Exploratory)** or **B (Exploitative)**, which determines the values of `mutation_rate` and `mutation_strength`.
        - **Evaluation Ticks**: `3,000` or `8,000`.
    b. The controller randomly initializes a population of `20` network individuals.

2.  **Evolution Loop**:
    a. Start an evolution that lasts for `G = 30` generations.
    b. In each generation `g`:
        i.   **Parallel Evaluation**: For the `20` individuals in the population, `20` independent, parallel simulation environments are started.
        ii.  Each individual `j` runs a full evaluation episode in its dedicated environment. The duration of the episode is determined by the `eval_ticks` parameter of that experimental group (`3,000` or `8,000` ticks).
        iii. After the episode ends, the `UnifiedRewardSystem` calculates the fitness score `f_j` for individual `j` based on the reward mode (`step` or `global`) specified by the experimental group.
        iv.  **Evolutionary Operations**: Once the fitness scores for all individuals have been calculated, the controller performs a full evolutionary operation (selection, crossover, mutation) based on the mutation configuration (`A` or `B`) of the experimental group to generate a new offspring population.
        v.   The new offspring population becomes the starting population for the next generation `g+1`.

3.  **Model Saving**:
    a. At the end of each generation, the algorithm saves the individual with the highest fitness in that generation as the best model of that generation.
    b. After all `30` generations of evolution are complete, the model with the highest historical fitness score among all generations' best models is selected and saved as the final model for that experimental group.

# 3.5.3 DRL Model Hyperparameter Settings

To ensure the reproducibility and validity of the DRL experiments in this study, this section details the key hyperparameters used in training the `DQN` and `NERL` controllers. These parameter settings are based on preliminary convergence and stability experiments and remain fixed during formal training.

### 1. Common Neural Network Architecture

To ensure a fair comparison between the baseline (DQN) and the core method (NERL), both employ the exact same neural network architecture. This architecture strikes a balance between the model's expressive power and computational efficiency, sufficient for the traffic control problem in this study.

| Layer | Type | Input Dim | Output Dim | Activation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Input Layer | 17 | 17 | - |
| 2 | Fully Connected (FC 1) | 17 | 128 | ReLU |
| 3 | Fully Connected (FC 2) | 128 | 64 | ReLU |
| 4 | Output Layer | 64 | 6 | - |


### 2. DQN-Specific Hyperparameters

The following table lists the main hyperparameters used for the `DQN` controller (experimental groups 3, 4) during training.

| Hyperparameter | Code Variable | Value | Description |
| :--- | :--- | :--- | :--- |
| Learning Rate | `learning_rate` | 5e-4 | The learning rate for the Adam optimizer. |
| Gamma | `gamma` | 0.99 | The discount factor for future rewards. A value closer to 1 indicates a greater emphasis on long-term returns. |
| Initial Epsilon | `epsilon` | 1.0 | The initial probability of choosing a random action at the beginning of training. |
| Epsilon Min | `epsilon_min` | 0.01 | The lower bound for epsilon decay. |
| Epsilon Decay | `epsilon_decay` | 0.9995 | The exponential decay rate by which epsilon is multiplied after each training step. |
| Replay Memory Size | `memory_size` | 50,000 | The maximum number of $(s, a, r, s')$ transition samples stored. |
| Batch Size | `batch_size` | 8,192 | The number of samples to draw from memory for each network update. |
| Target Network Update Freq | `target_update_freq` | 1,000 | The frequency (in training **steps**) at which the policy network weights are copied to the target network. |

### 3. NERL-Specific Hyperparameters

The following table lists the main hyperparameters used for the `NERL` controller (experimental groups 5-12) during evolution. The mutation rate and mutation strength vary according to the **Exploratory (A)** and **Exploitative (B)** variants defined in **Section 3.6.1**.

| Hyperparameter | Code Variable | Variant A (Exploratory) | Variant B (Exploitative) | Description |
| :--- | :--- | :--- | :--- | :--- |
| Population Size | `population_size` | 20 | 20 | The number of individuals (neural networks) in each generation. |
| Elite Ratio | `elite_ratio` | 0.2 | 0.2 | The proportion of the fittest individuals directly preserved in each generation. |
| Tournament Size | `tournament_size` | 4 | 4 | The number of individuals randomly compared in each tournament selection. |
| Crossover Rate | `crossover_rate` | 0.8 | 0.8 | The probability of two parent individuals undergoing genetic crossover. |
| Mutation Rate | `mutation_rate` | **0.3** | **0.1** | The base probability of an individual's genes (network weights) undergoing mutation. |
| Mutation Strength | `mutation_strength` | **0.2** | **0.05** | The standard deviation of Gaussian mutation, controlling the magnitude of the mutation. |
| Evaluation Ticks | `eval_ticks` | 3000 / 8000 | 3000 / 8000 | The duration (in ticks) for evaluating each individual. |

These hyperparameters collectively define the learning behavior of the two DRL methods and are an important basis for subsequent experimental analysis and result comparison.

### 4. Unified Reward System Hyperparameters

To ensure the reproducibility of the research, the following table details the specific weight values defined in `ai/unified_reward_system.py` used to calculate the Step Reward and Global Reward.

**Table 3.5.2: Unified Reward System Weights and Parameters**

| Parameter Type | Parameter Name (Code Variable) | Value | Brief Description |
| :--- | :--- | :--- | :--- |
| **Global Reward** | `completion_bonus` | 200.0 | Base reward for completing one order |
| | `energy_scale_factor` | 100.0 | Scaling factor for energy cost to balance units |
| | `time_penalty_per_tick`| 0.1 | Base time cost per time tick |
| | `spillback_penalty_weight`| 0.1 | Penalty weight for picking station spillback |
| | `no_spillback_bonus` | 5.0 | Additional bonus for no spillback situation |
| | `spillback_queue_threshold`| 5.0 | Queue length threshold to trigger spillback penalty |
| **Step Reward** | `pass_high_priority` | 1.0 | Reward for a high-priority robot passing |
| | `pass_medium_priority`| 0.7 | Reward for a medium-priority robot passing |
| | `pass_low_priority` | 0.5 | Reward for a low-priority robot passing |
| | `wait_time_cost_high_priority` | 0.05 | Waiting cost for a high-priority robot |
| | `wait_time_cost_medium_priority` | 0.02 | Waiting cost for a medium-priority robot |
| | `wait_time_cost_low_priority` | 0.01 | Waiting cost for a low-priority robot |
| | `switch_penalty` | 0.1 | Fixed cost for a signal switch |
| **Step Reward (Enhanced)** | `critical_weight` | 2.0 | Reward/cost multiplier for critical intersections |

# 4.2 Training Process Analysis

To deeply understand the dynamic behavior of deep reinforcement learning models during the training process, this section will not only present the final performance metrics but also conduct a detailed quantitative analysis of their learning trajectories. A key analytical tool is **Evolution Trend Analysis**, which helps us objectively assess whether the model is continuously improving in the desired direction.

### Calculation and Interpretation of Trend Line Slope

In the following sections, we will analyze the evolution process of several Key Performance Indicators (KPIs), such as fitness, order completion rate, and energy per order. To quantify the trend of these indicators as generations evolve, we use **Ordinary Least Squares Linear Regression** to fit a trend line.

For a given KPI time-series data $(x_i, y_i)$, where $x_i$ is the generation number and $y_i$ is the corresponding KPI value for that generation, linear regression aims to find a line $y = mx + c$ that minimizes the sum of the squared residuals between the observed and predicted values.

$$
\min_{m, c} \sum_{i=1}^{N} (y_i - (mx_i + c))^2
$$

We are most interested in the **slope** $m$ of this fitted line. This slope is calculated in `analysis/paper_analyzer.py`, and its mathematical meaning represents the **average change per generation**.

-   **Positive slope ($m > 0$)**: Indicates that the KPI shows an **increasing trend** during the evolution process.
-   **Negative slope ($m < 0$)**: Indicates that the KPI shows a **decreasing trend** during the evolution process.
-   **Slope close to 0**: Indicates that the KPI has no significant increasing or decreasing trend throughout the evolution process and is relatively stable.

By calculating the slope, we can transform a visual intuition into a quantifiable metric, allowing for a more objective assessment of whether the model's learning is a **Desirable Trend** or an **Undesirable Trend**. For example, for "fitness," we expect to see a positive slope; whereas for "energy per order," we expect to see a negative slope. This method will be extensively used in `4.2.1` to analyze the evolution process of NERL.

# 4.2.1 NERL Evolution Process Analysis

Before verifying the final performance of the NERL controller, it is necessary to examine its evolutionary dynamics during the training process. This analysis helps to understand whether the model is learning effectively, whether the population is converging, and the specific impact of different hyperparameter configurations on the learning process. This section will use the `NERL-S-A3` group as a baseline case to conduct a quantitative trend analysis of several key performance indicators (KPIs) during its evolution.

### 1. Baseline Case Analysis: Multi-dimensional Evolution Trend of the High-Exploration Variant (`A`)

Figure 4.2.1 shows the performance of the elite individuals of the `NERL-S-A3` experimental group over 30 generations of evolution on three core KPIs: Best Fitness, Completion Rate, and Energy per Order.

| (a) Best Fitness | (b) Completion Rate | (c) Energy per Order |
|:---:|:---:|:---:|
|Insert Image A here|Insert Image B here|Insert Image C here|
*Figure 4.2.1: Evolution trends of the elite individuals of the `NERL-S-A3` group on (a) Best Fitness, (b) Completion Rate, and (c) Energy per Order.*

According to the trend analysis, the evolution slope and trend assessment for each indicator are as follows:

- **Best Fitness**: `Slope = +1594.24` (Desirable Trend)
- **Completion Rate**: `Slope = +0.0008` (Desirable Trend)
- **Energy per Order**: `Slope = -2.69` (Desirable Trend)
- **Signal Switch Count**: `Slope = +3.58` (Undesirable Trend)

From the data and charts, the following points can be summarized:

1.  **Effective Learning and Optimization**: As shown in Figure 4.2.1(a), the **fitness** of the elite individuals shows a significant upward trend (slope `+1594`), proving that the evolutionary algorithm effectively guided the model towards maximizing the reward function (defined in Section 3.4.5). This macroscopic score improvement is supported by specific sub-goals. Although the **order completion rate** in Figure 4.2.1(b) fluctuates, the trend line is still positive (slope `+0.0008`), while the **energy per order** in Figure 4.2.1(c) shows a significant and continuous downward trend (slope `-2.69`). These two points together indicate that the model not only learned to complete more orders but also learned to do so in a more energy-efficient manner, meaning the design of the reward function achieved its intended effect.

2.  **Trade-off & Evolution of Strategy**: An interesting phenomenon is the evolutionary trend of the **Signal Switch Count**. Although the step reward design includes a penalty term for "phase switching" ($C_{\text{switch}}$), the data shows that the slope of this indicator is positive (`+3.58`), meaning the model tends to switch traffic signals more frequently. This is not a failure of learning but a manifestation of the agent's autonomous decision-making. This phenomenon reveals that during the learning process, the model discovered that **the local penalty incurred by moderately increasing phase switches could be exchanged for a significant improvement in traffic fluidity, thereby obtaining a much larger global benefit (higher order completion rate and lower waiting times) that far outweighs the penalty.** This complex trade-off behavior, sacrificing a local metric for macroscopic optimality, is difficult for traditional rule-based controllers to achieve.

3.  **The Cost and Value of Exploration**: The drastic fluctuations in the order completion rate in Figure 4.2.1(b) show that the highly exploratory A group was trying different strategies in each generation. The attempts of some generations might be unsuccessful (like the sharp drop in generations 9-10), but this breadth of exploration is the foundation for eventually finding an efficient and energy-saving strategy (like the stable high point after generation 25).

In summary, the analysis of the baseline case shows that NERL can not only successfully learn and optimize multiple core KPIs but can also exhibit complex strategic trade-off capabilities.

### 2. Comparative Analysis: The Impact of Different Evolutionary Configurations

To further understand the role of various hyperparameters, we compare the baseline case with other representative experimental groups.

#### a. Reward Mode: Step vs Global

When comparing different reward modes, an important premise is that one should not directly compare the absolute values or slopes of their "Fitness," because the calculation methods and numerical scales of `Step Reward` and `Global Reward` are completely different.

Therefore, the focus of this section is to analyze how these two reward modes, as driving forces for training, respectively affect the common key performance indicators (KPIs)—that is, the final actual operational performance. For this purpose, we will compare the `NERL-S-A3` group with the `NERL-G-A3` group.

**[Figure Suggestion: Figure 4.2.2 - Comparison of Evolution Trends of Key Performance Indicators under Different Reward Modes (Step vs. Global)]**

To conduct a quantitative comparison, Table 4.2.1 summarizes the evolution trend slopes of the two experimental groups on core output and efficiency indicators.

| Experimental Group | Reward Mode | Key Performance Indicator (KPI) | Evolution Trend Slope | Trend Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **`NERL-S-A3`** | **Step** | **Order Completion Rate** | **`+0.000825`** | **Desirable Trend** |
| `NERL-G-A3` | Global | Order Completion Rate | `-0.000698` | Undesirable Trend |
| **`NERL-S-A3`** | **Step** | **Energy per Order** | **`-2.695533`** | **Desirable Trend** |
| `NERL-G-A3` | Global | Energy per Order | `-0.720350` | Desirable Trend |
*Table 4.2.1: Comparison of evolution trend slopes for order completion rate and energy per order between Step Reward and Global Reward.*

From the data analysis, the following two conclusions can be drawn:

1.  **Guidance of Step Reward on Output Improvement**:
    Order completion rate is a direct measure of the system's core output. As shown in Table 4.2.1, the `NERL-S-A3` group, using step rewards, shows a positive development trend in its completion rate (slope `+0.000825`), indicating that its dense, real-time reward signals successfully guided the agent to learn strategies that effectively improve the system's overall output. In contrast, the `NERL-G-A3` group, using global rewards, shows a negative trend in its completion rate (slope `-0.000698`). This phenomenon indicates that under the current training settings, relying solely on sparse, delayed global rewards makes it difficult for the agent to establish an effective credit assignment between microscopic decisions and macroscopic outcomes, leading to a noisy learning signal.

2.  **Driving Force of Step Reward on Efficiency Optimization**:
    The data shows that although the energy per order decreased in both groups, the downward slope of the step reward group (A) (`-2.69`) is much steeper than that of the global reward group (C) (`-0.72`). This means that the step reward not only guided the model to complete orders but also drove it to do so in a more energy-efficient manner.

In summary, the experimental evidence supports the effectiveness of the step reward mode in guiding the NERL controller to learn complex warehousing tasks. It not only ensures that the model evolves towards improving the system's total output but also discovers optimization potential in operational details more efficiently.

#### b. Impact of Exploration Strategy: High Exploration (A) vs. Low Exploration (B)

In neuroevolution, the diversity of the population and the exploration intensity of individuals are key determinants of whether the algorithm can escape local optima. This section aims to investigate the impact of exploration strategy hyperparameter settings in the NERL controller on the evolutionary results. We will compare two experimental groups that use the same step reward but have different exploration intensities: `NERL-S-A3` and `NERL-S-B3`.

**[Figure Suggestion: Figure 4.2.3 - Comparison of Evolution Trends of Key Performance Indicators under Different Exploration Intensities (High vs. Low)]**

Table 4.2.2 summarizes the evolution trends of key indicators under high and low exploration intensity configurations.

| Experimental Group | Exploration Intensity | Key Performance Indicator (KPI) | Evolution Trend Slope | Trend Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **`NERL-S-A3`** | **High** | **Order Completion Rate** | **`+0.000825`** | **Desirable Trend** |
| `NERL-S-B3` | Low | Order Completion Rate | `-0.000334` | Undesirable Trend |
| **`NERL-S-A3`** | **High** | **Fitness** | **`+1594.24`** | **Desirable Trend** |
| `NERL-S-B3` | Low | Fitness | `+693.45` | Desirable Trend |
| `NERL-S-A3` | High | Energy per Order | `-2.695533` | Desirable Trend |
| `NERL-S-B3` | Low | Energy per Order | `-1.753562` | Desirable Trend |
*Table 4.2.2: Comparison of evolution trend slopes on core KPIs between High Exploration (A) and Low Exploration (B).*

The core conclusion from the data analysis is: **Insufficient exploration may lead to premature convergence to a local optimum, or even get stuck in a policy that cannot improve system output.**

1.  **Impact on System Output**:
    As shown in Table 4.2.2, the high-exploration `NERL-S-A3` group shows an increasing trend in order completion rate (slope `+0.000825`); however, the low-exploration `NERL-S-B3` group shows a decreasing trend (slope `-0.000334`). This phenomenon illustrates that in complex traffic control problems, if the agent's exploration is insufficient and it dares not try behaviors that might temporarily reduce efficiency, it may become trapped in an inefficient policy. The evolution of group B may have converged to a suboptimal policy of "stagnating traffic to avoid any potential collision risk," ultimately harming the overall system goal.

2.  **Breadth and Potential of Learning**:
    The growth slope of Fitness also corroborates this view. The fitness growth rate of the `NERL-S-A3` group (slope `+1594`) is more than double that of the `NERL-S-B3` group (slope `+693`). This does not mean that group A's learning efficiency is higher, but that its "learning horizon" is broader. Higher exploration allows the population to search in a wider policy space. Although the process may be accompanied by greater fluctuations, this breadth is a necessary prerequisite for discovering efficient policies. Group B is also learning, but its search range is too narrow, limiting its optimization potential.

In summary, this comparative analysis highlights the importance of setting sufficient exploration intensity in the NERL framework. For tasks that require solving complex trade-off problems, giving the evolutionary process enough freedom to explore is a necessary path to an efficient and robust solution.

#### c. Impact of Evaluation Duration: 3000 Ticks vs. 8000 Ticks

The evaluation duration (`evaluation_ticks`) determines the time each agent interacts with the environment to demonstrate the quality of its policy during evolution. This section analyzes the actual impact of the evaluation duration on learning effectiveness by comparing the `NERL-S-A3` and `NERL-S-A8` groups.

**[Figure Suggestion: Figure 4.2.4 - Comparison of Evolution Trends of Key Performance Indicators under Different Evaluation Durations (3000 vs. 8000 ticks)]**

Table 4.2.3 summarizes the evolution trends of key indicators under the two evaluation duration configurations.

| Experimental Group | Evaluation Ticks | Key Performance Indicator (KPI) | Evolution Trend Slope | Trend Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **`NERL-S-A3`** | **3000** | **Order Completion Rate** | **`+0.000825`** | **Desirable Trend** |
| `NERL-S-A8` | 8000 | Order Completion Rate | `-0.001454` | Undesirable Trend |
| **`NERL-S-A3`** | **3000** | **Energy per Order** | **`-2.695533`** | **Desirable Trend** |
| `NERL-S-A8` | 8000 | Energy per Order | `+0.064461` | Undesirable Trend |
| **`NERL-S-A3`** | **3000** | **Signal Switch Count** | **`+3.583537`** | **Undesirable Trend** |
| `NERL-S-A8` | 8000 | Signal Switch Count | `-3.322136` | Desirable Trend |
*Table 4.2.3: Comparison of evolution trend slopes on core KPIs between 3000 Ticks (`NERL-S-A3`) and 8000 Ticks (`NERL-S-A8`) evaluation durations.*

The data analysis results indicate that: **Simply extending the evaluation time may lead to a deterioration of the learning process; longer is not always better.**

1.  **Credit Assignment Delay and Reward Signal Dilution**:
    This is the core problem. In the design of the step reward (see Section 3.4.5), the agent receives immediate feedback at each time step. When the evaluation duration is extended from 3000 to 8000 ticks, the number of time steps in a full episode increases significantly, causing the reward from any specific, beneficial micro-action to be diluted over the long total duration. It becomes difficult for the agent to link the final outcome to a critical decision made thousands of steps earlier, which is a classic "credit assignment problem" in reinforcement learning. The success of the `NERL-S-A3` group lies in its relatively short evaluation window, which makes the causal chain between action and feedback clearer and the learning signal stronger.

2.  **Failure of Short-Sighted Penalties and Policy Drift**:
    A longer time window may also render certain penalty terms ineffective. For example, the penalty for phase switching, $C_{\text{switch}}$. Within a 3000-tick window, the cost of frequent switching is significant, and the agent must trade off between the "penalty of switching" and the "gain in fluidity" (as shown by the `+3.58` slope for the `NERL-S-A3` group). But on the scale of 8000 ticks, the agent might discover that by strenuously avoiding switching (as shown by the `-3.32` slope for the `NERL-S-A8` group) to accumulate small rewards, its overall fitness might still be higher, even if this leads to long-term traffic paralysis later on. The model may have learned a "short-sighted conservative policy," sacrificing the long-term, ultimate system goal to escape immediate, minor penalties.

In summary, this comparative analysis reveals an important principle for setting the evaluation duration: the evaluation window must match the design of the reward function and the time scale of the task itself. An appropriately sized evaluation window is necessary to ensure the effectiveness of the reward signal and the stability of the learning process.

### 3. Comprehensive Performance Comparison in the Training Phase

The preceding sections analyzed the impact of different hyperparameter configurations on the models' **evolutionary process (slope)**. However, the trend of the evolutionary process does not fully equate to the superiority of the final performance. This section shifts the perspective from "process" to "preliminary results." By horizontally comparing the performance of the **elite models** from each experimental group in their respective training evaluation scenarios at the end of training, we can examine the preliminary performance achieved by different strategy combinations and provide a reference for the more rigorous, standardized final validation in the next section.

**[Figure Suggestion: Figure 4.2.5 - Final Order Completion Rate Comparison of Elite Models from All NERL Experimental Groups in Training Evaluation]**
**[Figure Suggestion: Figure 4.2.6 - Final Energy per Order Comparison of Elite Models from All NERL Experimental Groups in Training Evaluation]**
**[Figure Suggestion: Figure 4.2.7 - Final Average Intersection Congestion Comparison of Elite Models from All NERL Experimental Groups in Training Evaluation]**
**[Figure Suggestion: Figure 4.2.8 - Final Signal Switch Count Comparison of Elite Models from All NERL Experimental Groups in Training Evaluation]**
**[Figure Suggestion: Figure 4.2.9 - Final Total Stop-and-Go Events Comparison of Elite Models from All NERL Experimental Groups in Training Evaluation]**

Through a comprehensive analysis of the above charts, several key observations can be made during the training phase. These observations depict the characteristics of different strategies, but their ultimate effectiveness remains to be validated:

1.  **Potential of Global Reward and Long Evaluation: The "Big Picture" Strategy on the Training Ground**
    A notable trend in the training phase evaluation is that the combination of "global reward + long evaluation," such as in groups `NERL-G-B3` and `NERL-G-B8`, shows strong potential in the two core metrics of **order completion rate** and **energy per order**.
    This reveals a possible mechanism: although the global reward signal is sparse, when given a sufficiently long evaluation time, the evolutionary algorithm has the space to explore grander, more complex long-term strategies. The agent is no longer bound by short-term step rewards but can "discover" strategies in the long evaluation that sacrifice short-term benefits for long-term returns. However, a major concern for the final validation in the next section is whether this highly adapted, complex strategy is too "delicate" and thus "fragile."

2.  **The "Short-Sighted" Risk of Step Reward: Policy Drift under Long Evaluation**
    In contrast, the step reward models that performed well in the 3000-tick short evaluation, such as `NERL-S-A8` and `NERL-S-B8`, showed mediocre order completion rates at the end of training when extended to 8000 ticks. This seems to confirm the hypothesis in subsection c, that there is a mismatch between step rewards and an overly long evaluation window. Within 8000 ticks, the agent might fall into a state of "Reward Hacking": excessively focusing on executing behaviors that maximize short-term, immediate step rewards, which in the long run may harm the ultimate goal of completing orders.

3.  **Performance Trade-off: The Aggressive Nature of High-Performing Models**
    From the charts of signal switch count and total stop-and-go events, it can be seen that the experimental groups that achieved higher order completion rates in the training evaluation, such as `NERL-G-A8` and `NERL-G-B8`, also had the most drastic internal disturbances in their traffic systems. This reveals that these models learned an "aggressive" management style, intervening frequently to improve flow efficiency. The effectiveness of this strategy highly depends on accurate prediction of the environment, and its stability will be tested when facing the longer, more unpredictable real validation scenarios.

**Summary and Outlook**: Synthesizing the analysis of the evolutionary process and the final state of training, a preliminary conclusion can be drawn: there is no single "optimal" hyperparameter configuration, but rather **strategy combinations** suitable for different objectives.
- The `global reward + long evaluation` combination learned the most promising, macroscopic, but perhaps most complex strategies during training.
- The `step reward + short evaluation` combination produced the most stable, but potentially less promising, strategies.

Will the characteristics and potential observed in the training environment translate into real strength under standardized, long-period validation? Which model's strategy has better **generalization ability** and **robustness**? The answers to these questions will be revealed in the final performance validation in the next section. This provides a clear, problem-oriented transition for us from "process analysis" to "final validation."

# 4.4 Chapter Summary

This chapter, through a series of systematic experiments, conducted an in-depth, multi-dimensional performance evaluation of rule-based baseline controllers, a standard Deep Reinforcement Learning (DQN) controller, and various Neuroevolution Reinforcement Learning (NERL) variants employed in this study. The analysis in this chapter follows a path from "macroscopic comparison" to "microscopic insight," and then to "systematic patterns," aiming to reveal the performance and applicability of different control philosophies in modern warehouse automation scenarios.

First, in the comprehensive performance comparison in Section `4.3.1`, this study observed that all controllers must trade off between "order completion rate" (output) and "energy consumption per order" (cost). The data clearly divides all controllers into three distinct strategic clusters: "High-Throughput," "Traditional Trade-off," and the "High Energy-Efficiency" cluster represented by the NERL method adopted in this study.

Second, in Sections `4.3.2` and `4.3.3`, this chapter delved into the intrinsic differences between different controller families. The analysis showed that:
1.  **Baseline and DQN controllers** tend towards "single-point optimization." They excel at maximizing a single objective (like order completion rate), but this often comes with higher energy consumption, reflecting a certain limitation in multi-objective scenarios.
2.  A notable feature of the **NERL controllers** is their performance in "multi-objective trade-offs." Through its evolutionary mechanism, it explored and learned strategies different from traditional methods, achieving a significant improvement in energy efficiency with a slight decrease in completion rate, to some extent changing the traditional "output-energy" trade-off relationship.
3.  Further analysis revealed that by adjusting NERL's internal reward mechanism (`Global` vs. `Step`), its strategic characteristics can be influenced to obtain different performances, either emphasizing a "big picture view" or being adept at "opportunism."

Finally, the stability analysis in Section `4.3.4` provided a supplementary note to these "personalities." DQN is like a "stable expert," with highly predictable output; whereas NERL is like an "adaptive explorer," whose output fluctuates but its "intention" to save energy is more consistent.

In summary, the work of this chapter not only compared the performance of different controllers but also provided a framework for analyzing and understanding complex DRL systems. The experimental results show that in multi-objective optimization problems like those in the RMFS domain, there may be no absolute "best" controller, only the "most suitable" strategy. The purpose of this study is to systematically demonstrate how to understand, evaluate, and, by adjusting their internal mechanisms, obtain intelligent control strategies that meet the needs of different industrial scenarios (e.g., pursuing high output, high stability, or a better balance of energy efficiency). These observations provide a data-based reference and methodological insights for the application of DRL technology in related fields.

# 5.1 Research Summary

This study aims to investigate the problem of reduced operational efficiency due to traffic congestion in modern automated Robotic Mobile Fulfillment Systems (RMFS). To this end, this thesis focuses on comparing and analyzing several intelligent intersection traffic control strategies, with the goal of understanding the various possibilities for maximizing system order fulfillment capacity while minimizing ineffective robot waiting and energy consumption.

To achieve this goal, this study first constructed a high-fidelity warehouse simulation environment and designed two traditional rule-based controllers (time-based and queue-based) as performance baselines. Next, Deep Reinforcement Learning (DRL) methods were introduced, implementing a controller based on the standard Deep Q-Network (DQN) and another NERL controller that combines neuroevolution with reinforcement learning. For the NERL model, this study further designed multiple sets of controlled experiments covering different reward modes, exploration intensities, and evaluation durations to systematically investigate the impact of various hyperparameters on model behavior and performance.

The analysis of the experimental results revealed that when evaluating controller performance, both "order completion rate" (output) and "energy efficiency" (cost) must be considered. The study observed that different control strategies exhibit three distinct clusters in the trade-off space of these two dimensions: "High-Throughput," "Traditional Trade-off," and "High Energy-Efficiency."

The final observation of this study is that in such complex multi-objective optimization problems, there may not be a "best" controller applicable to all scenarios. Baseline and standard DQN methods tend to optimize for a single objective, excelling in output but with higher energy consumption. The NERL method adopted in this study demonstrated the ability to find different balance points in the trade-off space, particularly learning strategies with significantly improved energy efficiency. More importantly, the study shows that by adjusting NERL's internal reward mechanism, its learning direction can be actively guided to obtain controllers with different "personalities." This observation suggests that the key to understanding and applying DRL may lie in selecting or customizing the most "suitable" intelligent strategy based on specific operational needs (such as pursuing maximum throughput, lowest cost, or the best balance).

# 5.2 Major Findings

This study has yielded the following observations and findings through methodological exploration and experimental analysis.

On a theoretical level, a core observation of this study is that the experimental results clearly delineate the multi-objective trade-off landscape of the RMFS traffic control problem. The research shows that controller performance is not a one-dimensional matter of superiority or inferiority, but rather a positioning in the two-dimensional space formed by "output" and "energy consumption." This provides a more comprehensive perspective for understanding and evaluating such complex systems, suggesting that the value of a strategy should be assessed within the entire trade-off spectrum, rather than by merely comparing single metrics.

On a methodological level, the analysis process of this study demonstrates how different DRL algorithms can produce controllers with different strategic "personalities." The experimental results show that standard DQN tends to converge to an "expert-type" strategy with stable output but high energy consumption; whereas the NERL method adopted in this study is able to explore a more diverse policy space through its evolutionary mechanism. Particularly important, by comparing `Global` and `Step` rewards, this study provides a concrete case illustrating how Reward Engineering serves as an effective means to guide an agent to learn specific behavioral patterns that meet different needs.

On a practical application level, the analytical framework of this study provides a reference for warehouse operators when selecting or developing control strategies. The research results indicate that if the operational goal is to maximize short-term throughput, a simple baseline or standard DQN controller may suffice; however, if energy costs or equipment wear are significant considerations, adopting a method like NERL that can learn energy-saving strategies may offer a more cost-effective long-term operational solution. This emphasizes the importance of matching specific business needs with controller characteristics.

# 5.3 Research Limitations

Although this study has drawn a series of important conclusions through rigorous experimental design, it is necessary to acknowledge its several limitations. These limitations not only define the scope of applicability of the study's conclusions but also provide clear directions for future research.

First, one of the core limitations of this study is the inevitable Sim-to-Real Gap between the simulation environment and physical reality. Although all experiments in this study were conducted on a high-fidelity simulation platform, the platform cannot fully capture all the randomness and complexity of a real physical environment, such as unmodeled factors like hardware wear, sensor delays, or battery aging. These could all affect the performance of the controller when deployed in practice. Therefore, the optimal model derived from this study still requires field validation and calibration for its performance in a real physical environment.

Second, the conclusions of this study are based on a fixed warehouse layout and network structure, which constitutes another limitation on the generalizability of its conclusions. Although the chosen layout is representative, whether the conclusions about the optimal controller and its training configuration can be directly generalized to other warehouses with different topological structures remains to be empirically investigated, as different network structures may give rise to vastly different traffic bottlenecks and dynamic characteristics.

Furthermore, this study assumes that all robot agents are Homogeneous Agents, possessing identical physical and performance parameters. This allows the study's conclusions to be clearly attributed to the differences in the traffic control strategies themselves. However, this assumption does not account for the heterogeneity that exists in the real world due to factors like hardware aging, wear, or different calibrations, which could affect the overall dynamics of the fleet. Therefore, the findings of this study are more applicable to an idealized homogeneous robot fleet.

In addition, to focus on the core problem of intersection traffic control, this study made necessary simplifications to the task and traffic models. For example, more complex order structures or collaborative tasks between robots were not considered. These simplifications help to isolate variables for analysis but also mean that the controller in this study has not yet addressed higher-level systemic challenges.

Finally, there are limitations in the breadth of algorithms explored in this study. Although several representative controllers were compared, the field of deep reinforcement learning is developing rapidly. This study was unable to include other potentially powerful advanced algorithms like Proximal Policy Optimization (PPO) or Soft Actor-Critic (SAC) in the comparison. These algorithms might exhibit different characteristics in terms of sample efficiency or policy stability.

# 5.4 Future Work

Based on the findings of this study and the aforementioned limitations, future research can be explored in several directions to further advance the development of intelligent warehouse traffic control technology.

First, to address the Sim-to-Real Gap, a key future direction is to investigate how to transfer high-performance models trained in a simulation environment to real physical robot systems in a low-cost, high-efficiency manner. This may involve Domain Adaptation techniques, Fine-tuning models on a small amount of real data, or researching robust reinforcement learning algorithms that are less sensitive to changes in physical parameters, to enhance the feasibility of deploying the model in the field.

Second, to address the limitation of conducting the study in a single warehouse layout, future research should systematically evaluate the generalization ability of this study's optimal controller in diverse topological structures. Furthermore, one could study how to expose the DRL agent to a variety of layouts during training to learn a more general traffic control Meta-Policy that can autonomously adapt to different network structures. This is crucial for improving the algorithm's versatility.

Furthermore, as this study primarily focused on microscopic traffic control at intersections, a highly valuable extension is to integrate this study's traffic controller as a low-level execution module into a higher-level intelligent decision-making system. This system could be responsible for more macroscopic task allocation and dynamic path planning, even incorporating systemic factors like picking station congestion. This would allow for the exploration of hierarchical or multi-agent collaborative decision-making architectures to achieve deep, system-wide optimization.

In addition, to broaden the scope of algorithmic exploration in this study, future research should introduce modern DRL algorithms that have proven effective in other domains, such as Proximal Policy Optimization (PPO) and Soft Actor-Critic (SAC). A comprehensive performance comparison of these algorithms with the best-performing NERL model from this study will help to more clearly identify the strengths and weaknesses of different algorithms in solving the RMFS traffic problem.

Finally, to better align with the goals of green logistics, future models could integrate more refined energy dynamics models. For example, incorporating factors like the charge-discharge cycle life of batteries and energy consumption curves at different speeds into the reward function design could drive the agent to learn a more sustainable operational strategy that is not only energy-efficient but also helps to extend the service life of the hardware.

</rewritten_file>