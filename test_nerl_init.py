#!/usr/bin/env python3
"""測試 NERL 網路初始化"""
import torch
import sys
sys.path.append('.')
from ai.controllers.nerl_controller import EvolvableNetwork

# 測試網路初始化
print("測試 NERL 網路初始化...")
device = torch.device("cpu")

# 創建幾個網路
for i in range(3):
    net = EvolvableNetwork(17, 6, device)
    
    # 測試輸入
    test_input = torch.randn(1, 17)
    
    with torch.no_grad():
        output = net(test_input)
        print(f"\n網路 {i+1} 輸出: {output.numpy().flatten()}")
        
        # 檢查輸出層偏置
        print(f"輸出層偏置: {net.fc3.bias.data.numpy()}")

print("\n✅ 如果每個網路的輸出都不同，則初始化正確！")