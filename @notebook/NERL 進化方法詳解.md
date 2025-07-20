  NERL 進化方法詳解：

  1. 種群參數

  population_size=20      # 種群大小：20個個體
  elite_size=4           # 精英保留：保留最好的4個
  tournament_size=4      # 錦標賽大小：4個個體競爭
  crossover_rate=0.7     # 交叉率：70%機率進行交叉
  mutation_rate=0.15     # 變異率：15%的權重會變異
  mutation_strength=0.1  # 變異強度：高斯噪聲的標準差

  2. 進化流程 (_create_new_generation)

  A. 精英保留（Elitism）

  # 找出適應度最高的 4 個個體
  elite_indices = np.argsort(self.fitness_scores)[-self.elite_size:]
  # 直接複製到下一代
  for idx in elite_indices:
      new_population.append(copy.deepcopy(self.population[idx]))

  B. 產生剩餘個體（16個）

  有 70% 機率使用交叉，30% 機率使用變異複製：

  交叉（Crossover）- 70% 機率：
  # 1. 錦標賽選擇兩個父代
  parent1_idx = self._tournament_selection(4)  # 從4個中選最好的
  parent2_idx = self._tournament_selection(4)

  # 2. 均勻交叉產生子代
  child1 = self._crossover(parent1, parent2)
  child2 = self._crossover(parent2, parent1)

  # 3. 對子代進行變異
  child1 = self._mutate(child1)
  child2 = self._mutate(child2)

  變異複製 - 30% 機率：
  # 選擇一個父代並複製
  parent_idx = self._tournament_selection(4)
  child = copy.deepcopy(self.population[parent_idx])
  # 變異
  child = self._mutate(child)

  3. 選擇方法：錦標賽選擇

  def _tournament_selection(self, k=4):
      # 隨機選擇 k 個個體
      selected_indices = np.random.choice(population_size, size=k)
      # 返回其中適應度最高的
      return selected_indices[np.argmax(fitness_scores)]

  4. 交叉方法：均勻交叉

  def _crossover(self, parent1, parent2):
      # 獲取父代權重向量
      p1_weights = parent1.get_weights_as_vector()
      p2_weights = parent2.get_weights_as_vector()

      # 隨機生成 0/1 遮罩
      mask = np.random.random(p1_weights.shape) < 0.5

      # 50% 來自父代1，50% 來自父代2
      child_weights = np.where(mask, p1_weights, p2_weights)

  5. 變異方法：高斯變異

  def _mutate(self, individual):
      weights = individual.get_weights_as_vector()

      # 15% 的權重會被選中變異
      mutation_mask = np.random.random(weights.shape) < 0.15

      # 生成高斯噪聲（均值0，標準差0.1）
      noise = np.random.normal(0, 0.1, weights.shape)

      # 只對選中的權重加上噪聲
      weights = weights + mutation_mask * noise

  進化過程示意圖：

  第 N 代（20個個體）
      ↓
  評估適應度
      ↓
  排序（從差到好）
      ↓
  保留最好的 4 個（精英）
      ↓
  產生 16 個新個體：
    - 70%：選擇2個父代 → 交叉 → 變異 → 2個子代
    - 30%：選擇1個父代 → 複製 → 變異 → 1個子代
      ↓
  第 N+1 代（4個精英 + 16個新個體 = 20個）

  這種進化方法的特點：

  1. 保證不退化：精英保留確保最好的個體不會丟失
  2. 探索與利用平衡：
    - 交叉：結合好的特徵
    - 變異：探索新的可能性
  3. 選擇壓力適中：錦標賽大小 4/20 = 20%，不會太激進
  4. 漸進式改進：每代都有機會產生更好的個體

  這就是為什麼 NERL 能夠逐步學習到好的交通控制策略！
