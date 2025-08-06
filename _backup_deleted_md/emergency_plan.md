# 緊急 5 天救援計劃

## Day 1 (今天剩餘時間)
- [ ] 備份所有現有數據
- [ ] 確認訂單生成參數（恢復原始密度）
- [ ] 開始 NERL step 模式快速訓練（overnight）

## Day 2 
- [ ] 早上檢查 NERL 訓練結果
- [ ] 開始 DQN step 模式訓練
- [ ] 下午開始 NERL global 訓練
- [ ] 準備並行評估環境

## Day 3
- [ ] 早上執行並行評估（8個模擬同時跑）
- [ ] 使用減少的 I/O 版本加速評估
- [ ] 下午分析初步結果

## Day 4
- [ ] 生成所有視覺化圖表
- [ ] 統計顯著性分析
- [ ] 準備論文數據表格

## Day 5
- [ ] 最終數據整理
- [ ] 論文圖表插入
- [ ] 結論撰寫

## 關鍵參數（已驗證有效）
```bash
# NERL 最佳參數
--generations 20
--population 30
--eval_ticks 2000
--parallel_workers 20

# DQN 快速收斂
--episodes 50
--training_ticks 100000
--learning_rate 0.001
```

## 重要提醒
1. 使用 SIMULATION_ID 環境變數避免檔案衝突
2. 每次訓練前清理 states/ 資料夾
3. 保持冷靜，相對比較仍然有效！