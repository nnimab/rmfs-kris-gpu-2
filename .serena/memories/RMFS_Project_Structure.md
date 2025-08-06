# RMFS 專案架構與核心模組分析

## 專案概述
RMFS（Robotic Mobile Fulfillment System）是一個混合式倉儲自動化系統，結合 Python 後端運算與 NetLogo 前端視覺化。專注於使用 NERL（神經進化強化學習）和 DQN（深度Q學習）優化交通控制。

## 核心架構特點
- **混合架構**：Python 計算 + NetLogo 視覺化
- **分散式控制**：每個路口獨立決策，但有自己的控制器實例
- **4 種控制器**：Time-based、Queue-based、DQN、NERL
- **統一獎勵系統**：支援 step/global 兩種模式

## AI 模組架構
### 控制器類別
- `DQNController`：深度Q學習，17維輸入，6個動作
- `NEController`：神經進化，支援種群進化
- `QueueBasedController`：基於隊列長度決策
- `TimeBasedController`：固定時間切換基準

### 獎勵系統
- `UnifiedRewardSystem`：591行複雜邏輯，混合V3/V6/V7版本
- 關鍵路口權重：[0,6,12,18,24,30,36,42,48,54,60]
- V7支援限速控制（6動作空間）

## 倉儲世界模組
### 實體管理
- Robot、Pod、Station、Intersection、Job、Order
- 各有對應的Manager類別負責管理

### 核心類別
- `Warehouse`：整合所有管理器，實現CSV批量優化
- `SpeedLimitManager`：V7新增走廊級限速

## 關鍵問題
1. **獎勵函數複雜度**：591行需簡化到50-100行
2. **資料收集不一致**：訓練與評估機制不同
3. **模型版本混亂**：缺乏清晰版本管理

## 已完成優化
- CSV批量寫入與進程隔離
- 神經網路架構增強（17→128→64→3）
- 修復訓練統計收集問題
- 清理65個臨時/測試檔案