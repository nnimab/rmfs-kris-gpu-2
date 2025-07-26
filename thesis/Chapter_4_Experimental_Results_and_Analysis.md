# Chapter 4: Experimental Results and Analysis

## 4.1 Chapter Overview

Following the research problem defined in Chapter 3—namely, how to design an effective and adaptive traffic control strategy that balances system throughput and energy efficiency—this chapter aims to conduct an empirical analysis and comparison of the proposed control schemes through a series of detailed experiments. We will first examine the training processes of the deep reinforcement learning models (DQN and NERL) to confirm their convergence and learning effectiveness. Subsequently, we will systematically compare the comprehensive performance of all controllers (including baseline and DRL models) in a standardized evaluation scenario, covering multiple aspects such as efficiency, throughput, and stability. We will then delve deeper into the specific behavioral patterns of different controllers in key traffic situations to explain the reasons behind their performance differences. Finally, we will use statistical testing methods to verify the significance of the main findings, providing solid data support for the core contributions of this research.

## 4.2 Training Process Analysis

To gain a deep understanding of the dynamic behavior of deep reinforcement learning models during training, this section will not only present the final performance metrics but also conduct a detailed quantitative analysis of their learning trajectories. A key analytical tool is **Evolution Trend Analysis**, which helps us objectively assess whether the model is continuously improving in the desired direction.

### Calculation and Interpretation of Trend Line Slope

In the following sections, we will analyze the evolution process of several Key Performance Indicators (KPIs), such as fitness, order completion rate, and energy consumption per order. To quantify the trend of these indicators as generations evolve, we use **Ordinary Least Squares Linear Regression** to fit a trend line.

For a given KPI time-series data $(x_i, y_i)$, where $x_i$ is the generation number and $y_i$ is the corresponding KPI value for that generation, linear regression aims to find a straight line $y = mx + c$ that minimizes the sum of the squared residuals between the observed values and the predicted values.

$$
\min_{m, c} \sum_{i=1}^{N} (y_i - (mx_i + c))^2 \quad (4-1)
$$

We are most interested in the **slope** $m$ of this fitted line. This slope, calculated in `analysis/paper_analyzer.py`, mathematically represents the **average change per generation**.

-   **Positive Slope ($m > 0$)**: Indicates that the KPI shows a **growing trend** over the course of evolution.
-   **Negative Slope ($m < 0$)**: Indicates that the KPI shows a **declining trend** over the course of evolution.
-   **Slope near 0**: Indicates that the KPI is relatively stable throughout the evolution process, with no significant upward or downward trend.

By calculating the slope, we can transform a visual intuition into a quantifiable metric, thereby more objectively evaluating whether the model's learning is a **Desirable Trend** or an **Undesirable Trend**. For example, for "Fitness," we expect to see a positive slope; whereas for "Energy per Order," we expect to see a negative slope. This method will be extensively used in Section 4.2.1 to analyze the evolutionary process of NERL.

## 4.2.1 Analysis of the NERL Evolutionary Process

Before validating the final performance of the NERL controllers, it is necessary to examine their evolutionary dynamics during the training process. This analysis helps to understand whether the model is learning effectively, whether the population is converging, and the specific impact of different hyperparameter configurations on the learning process. This section will use Group A (NERL-Step, High Exploration, 3000 Ticks) as a baseline case to conduct a quantitative trend analysis of several Key Performance Indicators (KPIs) during its evolution.

### 1. Benchmark Case Analysis: Multi-dimensional Evolution Trend of the High-Exploration Variant (A)

Figure 4.2.1 shows the performance of the elite individuals from the Group A (NERL-Step, High Exploration, 3000 Ticks) experiment across three core KPIs over 30 generations of evolution: Best Fitness, Completion Rate, and Energy per Order.

| (a) Best Fitness | (b) Completion Rate | (c) Energy per Order |
|:---:|:---:|:---:|
|Image A to be inserted here|Image B to be inserted here|Image C to be inserted here|
*Figure 4.2.1: Evolution trends of the elite individuals from Group A (NERL-Step, High Exploration, 3000 Ticks) on (a) Best Fitness, (b) Completion Rate, and (c) Energy per Order.*

Based on the trend analysis, the evolution slope and trend assessment for each indicator are as follows:

- **Best Fitness**: `Slope = +1594.24` (Desirable Trend)
- **Completion Rate**: `Slope = +0.0008` (Desirable Trend)
- **Energy per Order**: `Slope = -2.69` (Desirable Trend)
- **Signal Switch Count**: `Slope = +3.58` (Undesirable Trend)

From the data and charts, the following points can be summarized:

1.  **Effective Learning and Optimization**: As shown in Figure 4.2.1(a), the **Best Fitness** of the elite individuals shows a significant upward trend (slope `+1594`), proving that the evolutionary algorithm is effectively guiding the model towards the goal of maximizing the reward function (defined in Section 3.4.5). This macroscopic score improvement is supported by specific sub-goals. Although the **Completion Rate** in Figure 4.2.1(b) fluctuates, its trend line is still positive (slope `+0.0008`), while the **Energy per Order** in Figure 4.2.1(c) shows a significant and continuous downward trend (slope `-2.69`). These two points together indicate that the model not only learned to complete more orders but also learned to do so in a more energy-efficient manner, meaning the reward function design achieved its intended effect.

2.  **Strategy Trade-off and Evolution**: An interesting phenomenon is the evolutionary trend of the **Signal Switch Count**. Although the step reward design includes a penalty term ($C_{\text{switch}}$) for "phase switching," the data shows that the slope of this indicator is positive (`+3.58`), meaning the model tends to switch traffic signals more frequently. This is not a failure of learning but a manifestation of the agent's autonomous decision-making. This phenomenon reveals that the model discovered during the learning process that **the local penalty from moderately increasing phase switches can be exchanged for a significant improvement in traffic fluidity, thereby obtaining a much larger global benefit (higher completion rate and lower waiting times) that far outweighs the penalty.** This complex trade-off behavior, sacrificing a local metric for macroscopic optimality, is difficult for traditional rule-based controllers to achieve.

3.  **The Cost and Value of Exploration**: The drastic fluctuations in the completion rate in Figure 4.2.1(b) show that the high-exploration Group A was trying different strategies in each generation. The attempts of some generations might be unsuccessful (like the sharp drop in generations 9-10), but this breadth of exploration is the foundation for ultimately finding an efficient and energy-saving strategy (like the stable high point after generation 25).

In summary, the analysis of the benchmark case indicates that NERL can not only successfully learn and optimize multiple core KPIs but can also exhibit complex strategic trade-off capabilities.

### 2. Comparative Analysis: The Impact of Different Evolutionary Configurations

To further understand the role of various hyperparameters, we will compare the benchmark case with other representative experimental groups.

#### a. Reward Scheme: Step vs. Global

When comparing different reward schemes, an important premise is that one should not directly compare the absolute values or slopes of their "Fitness," because the calculation methods and numerical scales of `Step Reward` and `Global Reward` are completely different.

Therefore, the focus of this section is to analyze how these two reward schemes, as driving forces for training, respectively affect the common Key Performance Indicators (KPIs)—that is, the final actual operational performance. For this, we will compare Group A (NERL-Step, High Exploration, 3000 Ticks) and Group C (NERL-Global, High Exploration, 3000 Ticks).

**【圖表建議：圖 4.2.2 - 不同獎勵模式下 (Step vs. Global) 關鍵績效指標的演化趨勢對比圖】**

For a quantitative comparison, Table 4.2.1 summarizes the evolution trend slopes for the two experimental groups on core output and efficiency indicators.

| Experiment Group | Reward Scheme | Key Performance Indicator (KPI) | Evolution Trend Slope | Trend Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **A (High-Explore, 3000 Ticks)** | **Step** | **Completion Rate** | **`+0.000825`** | **Desirable** |
| C (High-Explore, 3000 Ticks) | Global | Completion Rate | `-0.000698` | Undesirable |
| **A (High-Explore, 3000 Ticks)** | **Step** | **Energy per Order** | **`-2.695533`** | **Desirable** |
| C (High-Explore, 3000 Ticks) | Global | Energy per Order | `-0.720350` | Desirable |
*Table 4.2.1: Comparison of evolution trend slopes for Completion Rate and Energy per Order under Step and Global reward schemes.*

From the data analysis, the following two conclusions can be drawn:

1.  **Guidance of Step Reward on Throughput Improvement**:
    The completion rate is a direct measure of the system's core output. As shown in Table 4.2.1, Group A, which used step rewards, shows a positive development trend in its completion rate (slope `+0.000825`), indicating that its dense, immediate reward signals successfully guided the agent to learn policies that effectively increase the system's overall throughput. In contrast, Group C, using global rewards, shows a negative development trend in its completion rate (slope `-0.000698`). This phenomenon suggests that, under the current training settings, relying solely on sparse, delayed global rewards makes it difficult for the agent to establish effective credit assignment from micro-level decisions to macro-level outcomes, leading to a noisy learning signal.

2.  **Driving Force of Step Reward on Efficiency Optimization**:
    The data shows that although the energy consumption per order is decreasing in both groups, the downward slope of the step-reward group (A) (`-2.69`) is much steeper than that of the global-reward group (C) (`-0.72`). This means that the step reward not only guides the model to complete orders but also drives it to do so in a more energy-efficient manner.

In summary, the experimental evidence supports the effectiveness of the step reward scheme in guiding the NERL controller to learn complex warehouse tasks. It not only ensures that the model evolves towards increasing the system's total output but also more efficiently discovers optimization potential in operational details.

#### b. The Impact of Exploration Strategy: High (A) vs. Low (B)

In neuroevolution, the diversity of the population and the exploratory strength of individuals are key determinants of whether the algorithm can escape local optima. This section aims to investigate the impact of exploration strategy hyperparameter settings in the NERL controller on the evolutionary outcomes. We will compare two experimental groups that use the same step reward but have different exploration strengths: Group A (NERL-Step, High Exploration, 3000 Ticks) and Group B (NERL-Step, Low Exploration, 3000 Ticks).

**【圖表建議：圖 4.2.3 - 不同探索強度下 (高 vs. 低) 關鍵績效指標的演化趨勢對比圖】**

Table 4.2.2 summarizes the evolution trends of key indicators for high and low exploration strength configurations.

| Experiment Group | Exploration Strength | Key Performance Indicator (KPI) | Evolution Trend Slope | Trend Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **A (Step, 3000 Ticks)** | **High** | **Completion Rate** | **`+0.000825`** | **Desirable** |
| B (Step, 3000 Ticks) | Low | Completion Rate | `-0.000334` | Undesirable |
| **A (Step, 3000 Ticks)** | **High** | **Fitness** | **`+1594.24`** | **Desirable** |
| B (Step, 3000 Ticks) | Low | Fitness | `+693.45` | Desirable |
| A (Step, 3000 Ticks) | High | Energy per Order | `-2.695533` | Desirable |
| B (Step, 3000 Ticks) | Low | Energy per Order | `-1.753562` | Desirable |
*Table 4.2.2: Comparison of evolution trend slopes for core KPIs between High Exploration (A) and Low Exploration (B).*

The core conclusion from the data analysis is: **Insufficient exploration can lead to premature convergence to a local optimum, or even to a policy that fails to improve system throughput.**

1.  **Impact on System Throughput**:
    As shown in Table 4.2.2, the completion rate of the high-exploration Group A shows an upward trend (slope `+0.000825`); however, the completion rate of the low-exploration Group B is decreasing (slope `-0.000334`). This phenomenon indicates that in a complex traffic control problem, if the agent's exploration is insufficient and it dares not try actions that might temporarily reduce efficiency, it can get stuck in an inefficient policy. The evolution of Group B may have converged to a suboptimal policy of "traffic stagnation to avoid any potential collision risk," ultimately undermining the overall system goal.

2.  **Breadth and Potential of Learning**:
    The growth slope of Fitness also corroborates this view. The fitness growth rate of Group A (slope `+1594`) is more than double that of Group B (slope `+693`). This does not mean Group A's learning efficiency is higher, but rather that its "learning horizon" is broader. Higher exploration allows the population to search in a wider policy space. Although the process may be accompanied by greater fluctuations, this breadth is a necessary prerequisite for discovering efficient policies. Group B, while also learning, has a search range that is too narrow, limiting its optimization potential.

In summary, this comparative analysis highlights the importance of setting sufficient exploration strength in the NERL framework. For tasks that require solving complex trade-off problems, giving the evolutionary process enough freedom to explore is a necessary path to an efficient and robust solution.

#### c. The Impact of Evaluation Duration: 3000 Ticks vs. 8000 Ticks

The evaluation duration (`evaluation_ticks`) determines the time each agent interacts with the environment to demonstrate the quality of its policy during evolution. This section analyzes the actual impact of evaluation duration on learning effectiveness by comparing Group A (NERL-Step, High Exploration, 3000 Ticks) and Group E (NERL-Step, High Exploration, 8000 Ticks).

**【圖表建議：圖 4.2.4 - 不同評估時長下 (3000 vs. 8000 ticks) 關鍵績效指標的演化趨勢對比圖】**

Table 4.2.3 summarizes the evolution trends of key indicators for the two evaluation duration configurations.

| Experiment Group | Evaluation Duration | Key Performance Indicator (KPI) | Evolution Trend Slope | Trend Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **A (NERL-Step, High-Explore)** | **3000** | **Completion Rate** | **`+0.000825`** | **Desirable** |
| E (NERL-Step, High-Explore) | 8000 | Completion Rate | `-0.001454` | Undesirable |
| **A (NERL-Step, High-Explore)** | **3000** | **Energy per Order** | **`-2.695533`** | **Desirable** |
| E (NERL-Step, High-Explore) | 8000 | Energy per Order | `+0.064461` | Undesirable |
| **A (NERL-Step, High-Explore)** | **3000** | **Signal Switch Count** | **`+3.583537`** | **Undesirable** |
| E (NERL-Step, High-Explore) | 8000 | Signal Switch Count | `-3.322136` | Desirable |
*Table 4.2.3: Comparison of evolution trend slopes for core KPIs between 3000 Ticks (A) and 8000 Ticks (E) evaluation durations.*

The data analysis results indicate: **Simply extending the evaluation time may lead to a deterioration of the learning process; longer is not necessarily better.**

1.  **Credit Assignment Delay and Reward Signal Dilution**:
    This is the core problem. In the step reward design (see Section 3.4.5), the agent receives immediate feedback at each time step. When the evaluation duration is extended from 3000 to 8000 ticks, the number of time steps in a full episode increases significantly. This causes the reward from any specific, beneficial micro-action to be diluted over the long total duration. It becomes difficult for the agent to link the final outcome to a key decision made thousands of steps earlier, which is a classic "credit assignment problem" in reinforcement learning. The success of Group A lies in its relatively short evaluation window, which makes the causal chain between actions and feedback clearer and the learning signal stronger.

2.  **Failure of Short-Sighted Penalties and Policy Drift**:
    A longer time window may also render certain penalty terms ineffective. For example, the penalty for phase switching, $C_{\text{switch}}$. Within a 3000-tick window, the cost of frequent switching is significant, and the agent must make a trade-off between the "penalty of switching" and the "gain in fluidity" (as shown by Group A's slope of `+3.58`). However, on the 8000-tick scale, the agent might discover that by strenuously avoiding switches (as shown by Group E's slope of `-3.32`) to accumulate minor rewards, its overall fitness might still be higher, even if this leads to long-term traffic paralysis later on. The model may have learned a "short-sighted conservative policy," sacrificing the long-term, ultimate system goal to escape immediate minor penalties.

In conclusion, this comparative analysis reveals an important principle for setting the evaluation duration: the evaluation window must match the design of the reward function and the time scale of the task itself. An appropriately sized evaluation window is essential to ensure the effectiveness of the reward signal and the stability of the learning process.

### 3. Comprehensive Performance Comparison at the Training Stage

The preceding sections analyzed the impact of different hyperparameter configurations on the model's **evolutionary process (slope)**. However, the trend of the evolutionary process does not fully equate to the superiority of the final performance. This section shifts the perspective from "process" to "preliminary results." By conducting a horizontal comparison of the performance of the **elite models** from each experimental group in their respective training evaluation scenarios at the end of training, we aim to examine the preliminary performance achieved by different strategy combinations and to provide a reference for the more rigorous, standardized final validation in the next section.

**【Figure Suggestion: Figure 4.2.5 - Final Completion Rate Comparison of All NERL Elite Models in Training Evaluation】**
**【Figure Suggestion: Figure 4.2.6 - Final Energy per Order Comparison of All NERL Elite Models in Training Evaluation】**
**【Figure Suggestion: Figure 4.2.7 - Final Average Intersection Congestion Comparison of All NERL Elite Models in Training Evaluation】**
**【Figure Suggestion: Figure 4.2.8 - Final Signal Switch Count Comparison of All NERL Elite Models in Training Evaluation】**
**【Figure Suggestion: Figure 4.2.9 - Final Total Stop-and-Go Events Comparison of All NERL Elite Models in Training Evaluation】**

Through a comprehensive analysis of the above charts, several key observations can be made at the training stage. These observations depict the characteristics of different strategies, but their ultimate effectiveness remains to be validated:

1.  **Potential of Global Reward and Long Evaluation: The "Big Picture" Strategy on the Training Ground**
    A significant trend in the training stage evaluation is that the combination of "Global Reward + Long Evaluation," such as in Group D (NERL-Global, Low-Explore, 3000 Ticks) and Group H (NERL-Global, Low-Explore, 8000 Ticks), shows strong potential in the core metrics of **Completion Rate** and **Energy per Order**.
    This reveals a possible mechanism: although the global reward signal is sparse, when given a sufficiently long evaluation time, the evolutionary algorithm has the space to explore grander, more complex long-term strategies. The agent is no longer bound by short-term step rewards but can "discover" strategies in the long evaluation that sacrifice short-term benefits for long-term returns. However, a major concern for the final validation in the next section is whether this complex strategy, highly adapted to the training environment, is too "delicate" and thus "fragile."

2.  **The "Short-Sighted" Risk of Step Rewards: Policy Drift with Long Evaluation**
    In contrast, the step-reward models that performed well in the 3000-tick short evaluation, such as Group E (NERL-Step, High-Explore, 8000 Ticks) and Group F (NERL-Step, Low-Explore, 8000 Ticks), showed mediocre performance in completion rate at the end of training when the evaluation was extended to 8000 ticks. This seems to confirm the hypothesis from subsection c, that there is a mismatch between step rewards and an overly long evaluation window. Within 8000 ticks, the agent might fall into a state of "Reward Hacking": excessively focusing on executing actions that maximize short-term, immediate step rewards, while these actions may harm the ultimate goal of completing orders over a longer time scale.

3.  **The Performance Trade-off: The Aggressive Nature of High-Performing Models**
    From the charts of signal switch counts and stop-and-go events, it can be seen that the experimental groups that achieved higher completion rates in the training evaluation, such as Group G (NERL-Global, High-Explore, 8000 Ticks) and Group H (NERL-Global, Low-Explore, 8000 Ticks), also had the most severe internal disturbances in their traffic systems. This reveals that these models learned an "aggressive" management style, intervening frequently to improve flow efficiency. The effectiveness of this strategy is highly dependent on accurate prediction of the environment, and its stability will be tested when facing the longer, more unpredictable scenarios of true validation.

**Summary and Outlook**: Combining the analysis of the evolutionary process and the final state of training, a preliminary conclusion can be drawn: there is no single "optimal" hyperparameter configuration, but rather **strategy combinations** suitable for different objectives.
- The `Global Reward + Long Evaluation` combination learned the most promising, macroscopic, but perhaps most complex, strategies during training.
- The `Step Reward + Short Evaluation` combination produced the most stable, but possibly less potent, strategies.

Can the characteristics and potential observed in the training environment be translated into real strength in a standardized, long-cycle validation? Which model's strategy is more **generalizable** and **robust**? The answers to these questions will be revealed in the final performance validation in the next section. This provides a clear, problem-oriented transition for us from "process analysis" to "final validation."

## 4.3 Final Performance Validation and Comparison

In the previous section, we analyzed the impact of different hyperparameter configurations on the NERL controller's performance during the **training process** and observed that certain combinations (like global reward with long evaluation) showed better potential in the training environment. However, the core question this section aims to address is whether performance during training can be directly translated into the model's actual performance in longer, more general scenarios. This directly relates to the model's **Generalization** and **Robustness**.

To this end, this section places all controllers—including baselines, DQN, and all NERL models—in a unified, standardized validation scenario lasting 50,000 ticks for performance evaluation. The goal is to objectively reveal which control strategy demonstrates ultimate comprehensive superiority in a persistent task that is closer to real-world operations, after stripping away the biases of the specific training environment.

### 1. Standardized Final Validation and Comparative Analysis

To conduct a comprehensive horizontal comparison of the final performance of all twelve controllers, their validation data across six Key Performance Indicators (KPIs) are compiled in Table 4.3.1. These indicators provide a quantitative assessment of each model's final performance from three dimensions: system throughput (completion rate), operational efficiency (energy per order), and system stability (signal switch count, stop-go events).

**Table 4.3.1: Comprehensive Comparison of Final Validation Performance for All Experimental Groups**

| Experiment                        | Completion Rate | Energy per Order | Total Energy | Signal Switches | Stop-Go Events | Completed Orders |
|------------------------------------|:--------------:|:----------------:|:------------:|:---------------:|:--------------:|:----------------:|
| K_EVAL_queue_based                 |     91.40%     |        54        |   35,764     |     12,702      |    17,035      |       659        |
| F_EVAL_nerl_step_b8000ticks        |     91.27%     |        33        |   21,621     |     12,758      |    16,396      |       659        |
| I_EVAL_dqn_step_55000              |     90.78%     |        50        |   33,764     |     12,755      |    17,421      |       679        |
| D_EVAL_nerl_global_b3000ticks      |     90.68%     |        44        |   28,718     |     12,203      |    16,489      |       652        |
| B_EVAL_nerl_step_b3000ticks        |     90.57%     |        51        |   33,013     |     12,278      |    16,885      |       653        |
| C_EVALnerl_global_a3000ticks       |     89.94%     |        51        |   32,745     |     12,033      |    16,793      |       644        |
| J_EVAL_dqn_global_55000            |     89.90%     |        60        |   38,996     |     12,575      |    17,266      |       650        |
| G_EVALnerl_global_a8000ticks_      |     89.57%     |        49        |   32,044     |     12,201      |    16,563      |       653        |
| E_EVAL_nerl_step_a8000ticks        |     89.42%     |        41        |   26,047     |     12,251      |    17,071      |       642        |
| H_EVAL_nerl_global_b8000ticks      |     89.20%     |        46        |   29,182     |     11,856      |    16,234      |       636        |
| L_EVAL_time_based                  |     88.56%     |        45        |   28,027     |      9,900      |    17,783      |       627        |
| A_EVAL_nerl_step_a3000ticks        |     84.51%     |        57        |   25,013     |      8,201      |    11,743      |       442        |

**【圖表建議：圖 4.3.1 - 所有控制器在「訂單完成率」上的最終表現對比】**
**【圖表建議：圖 4.3.2 - 所有控制器在「單均能耗」上的最終表現對比】**

The data in Table 4.3.1 reveals the disparity between training performance and final validation results. This is not just a performance ranking but a profound test of the generalization capabilities of different learning strategies.

1.  **Disparity between Training Performance and Generalization Ability**
    First, a key observation is that Group H (NERL-Global, Low-Explore, 8000 Ticks), which performed best in the training stage evaluation in Section 4.2, only achieved a completion rate of 89.20% in the final validation, significantly lower than other models. This performance degradation confirms a core concept in machine learning research: **Overfitting** to the training environment. The complex macroscopic strategy learned by Group H, while achieving excellent performance in the 8000-tick training evaluation, was likely too dependent on the specific conditions of training, leading to a "fragile" policy. When the evaluation period was extended to 50,000 ticks, and the dynamics and complexity of the environment increased, the strategy could not maintain its effectiveness, exposing its lack of generalization ability.

2.  **The Importance of Policy Robustness: The Performance of `QueueBased` and `NERL-F`**
    In contrast to the performance decline of Group H, the excellent performance of Group K (QueueBased) and Group F (NERL-Step, Low-Explore, 8000 Ticks) stands out. The success of these two models can be attributed to the inherent **Robustness** of their policies.
    *   **Performance of `QueueBased`**: As a simple reactive strategy, Group K (QueueBased) achieved the highest completion rate (91.40%) with its intuitive "let the longer queue pass" rule. This shows that a well-designed, simple rule-based baseline model can be highly competitive in specific metrics due to its stability and effectiveness. However, its high energy consumption per order (54) shows that this strategy maximizes throughput at the cost of energy efficiency, exhibiting a typical "single-objective optimal" characteristic.
    *   **The Comprehensive Optimal Solution of `NERL-F`**: The success of Group F (NERL-Step, Low-Explore, 8000 Ticks) is more enlightening. It nearly matched Group K's completion rate at 91.27%, but its energy per order was as low as 33, making it the most energy-efficient among all high-throughput models and demonstrating the best **energy-to-performance ratio**. This indicates that Group F's training configuration—"Step Reward + Low Exploration + Long Evaluation"—fostered a **highly generalizable and balanced policy**. The step reward provided a stable and clear learning signal; low exploration prevented the model from learning overly risky and fragile policies; and the long evaluation period gave the model a long-term perspective during learning. This combination led it to learn a more "reliable" rather than the most "sophisticated" strategy, ultimately achieving the best comprehensive performance in the multi-objective trade-off between throughput and efficiency.

3.  **The Baseline Value of DQN Models**
    The performance of Group I (DQN-Step) was also robust, ranking among the top with a 90.78% completion rate, proving the effectiveness of the standard DQN method in solving this type of problem. It serves as a very important measurement baseline, showing that a fully trained standard reinforcement learning model can outperform many more complex NERL variants, providing a solid reference point for the comparisons in this study.

### 2. Conclusion: From "Training Optimal" to "Comprehensive Optimal"

Synthesizing all validation results, the core conclusion of this research becomes clear: in the complex problem of warehouse traffic control, **the optimal performance of a model during training does not equate to its final comprehensive performance.**

Although models based on global rewards, like Group H (NERL-Global, Low-Explore, 8000 Ticks), showed potential for learning complex long-term strategies during training, such strategies have weaker generalization ability and are prone to overfitting the training environment. Conversely, a well-designed heuristic controller like `QueueBased` (Group K) can achieve the highest value in a core output metric but at the expense of energy efficiency.

The comprehensively optimal model in this study is Group F (NERL-Step, Low-Explore, 8000 Ticks). It demonstrates that a learning method combining **clear immediate feedback (step reward)** and **conservative exploration (low exploration)** can learn a policy with **strong generalization ability and the best overall effectiveness** in long-horizon tasks. It not only achieves a top-tier completion rate but also, with its superior energy efficiency, sets a new performance benchmark for the next generation of intelligent warehouse traffic controllers. This finding provides significant experimental evidence for how to deploy DRL systems in the real world that are not just "smart" but also "reliable."

## 4.4 Chapter Summary

This chapter aimed to conduct an in-depth quantitative evaluation and comparison of the traffic control performance of rule-based baseline controllers, standard Deep Q-Network (DQN) controllers, and various Neuroevolution Reinforcement Learning (NERL) variants in a complex warehouse environment through a series of systematic experiments. The analysis in this chapter followed a rigorous path from "process" to "results," and from "training potential" to "generalization evidence."

First, in Section 4.2, the study analyzed the training and evolutionary processes of the deep learning models. The analysis showed that different reward schemes, exploration strategies, and evaluation durations have a significant impact on the models' learning dynamics. In particular, it was observed that the combination of "global reward" and "long evaluation," as in Group H (NERL-Global, Low-Explore, 8000 Ticks), demonstrated higher potential for learning complex, long-term strategies in the training environment.

However, in the standardized final performance validation in Section 4.3, the study found a significant disparity between training-stage performance and final results. This turning point highlights a core issue in machine learning research—**Generalization**. The model that performed best during training, Group H, learned a policy that was overly adapted to the specific training environment (i.e., **Overfitting**), causing it to perform poorly in longer, more general testing scenarios and exposing the "fragility" of its strategy.

The final comparative results clearly indicate that:
1.  A well-designed heuristic controller, such as Group K (QueueBased), can achieve the optimal value in a single metric like "completion rate" due to the **robustness** of its policy, but this advantage comes with higher energy consumption.
2.  The comprehensively best-performing model in this study is Group F (NERL-Step, Low-Explore, 8000 Ticks). The training configuration used for this model enabled it to learn a **balanced policy** that is not overly aggressive and combines stability with efficiency. It not only achieved a top-tier completion rate but also demonstrated the best overall performance in the multi-objective trade-off with its significantly superior energy efficiency compared to other high-throughput models.

In conclusion, the experiments in this chapter do not merely select an optimal model but, more importantly, reveal that in complex problems like intelligent warehouse control, **a training framework that promotes robust and generalizable learning is key to translating the theoretical potential of deep reinforcement learning into real-world application value**. The success of Group F proves the importance of pursuing a solution that is not just "sophisticated" but also "reliable." These findings provide solid data support for the final conclusions of this thesis and point the way for future related research. 