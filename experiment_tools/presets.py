"""
實驗預設配置
============

定義三種強度等級的實驗配置，基於 EXPERIMENT_WORKFLOW_GUIDE.md 的建議
"""

# --- NERL 超參數組合 ---
NERL_CONFIG_A = {
    'name': 'High-Exploration',
    'mutation_rate': 0.2,
    'crossover_rate': 0.7,
}
NERL_CONFIG_B = {
    'name': 'High-Exploitation',
    'mutation_rate': 0.1,
    'crossover_rate': 0.8,
}

# 實驗預設配置
EXPERIMENT_PRESETS = {
    "quick": {
        "name": "快速驗證",
        "description": "快速功能測試",
        "estimated_time": "10-30分鐘",
        "icon": "🔸",
        "training": {
            "dqn_ticks": 2000,
            "nerl_generations": 5,
            "nerl_population": 10,
            "nerl_eval_ticks": 1000,
            "reward_modes": ["step", "global"]
        },
        "evaluation": {
            "ticks": 5000,
            "repeats": 1,
            "seeds": [42],
            "controllers": "auto"  # 自動檢測所有可用控制器
        },
        "charts": {
            "generate": True,
            "types": ["basic"],
            "dpi": 150
        },
        "parallel": {
            "enabled": True,
            "max_workers": 2
        }
    },
    
    "standard": {
        "name": "標準實驗",
        "description": "研究使用標準",
        "estimated_time": "1-2小時",
        "icon": "🔸",
        "recommended": True,
        "training": {
            "dqn_ticks": 10000,
            "nerl_generations": 20,
            "nerl_population": 20,
            "nerl_eval_ticks": 2000,
            "reward_modes": ["step", "global"]
        },
        "evaluation": {
            "ticks": 15000,
            "repeats": 3,
            "seeds": [42, 123, 789],
            "controllers": "auto"
        },
        "charts": {
            "generate": True,
            "types": ["all"],
            "dpi": 300
        },
        "parallel": {
            "enabled": True,
            "max_workers": 4
        }
    },
    
    "complete": {
        "name": "完整實驗",
        "description": "論文發表標準",
        "estimated_time": "3-5小時",
        "icon": "🔸",
        "training": {
            "dqn_ticks": 20000,
            "nerl_generations": 50,
            "nerl_population": 25,
            "nerl_eval_ticks": 3000,
            "reward_modes": ["step", "global"]
        },
        "evaluation": {
            "ticks": 30000,
            "repeats": 5,
            "seeds": [42, 123, 789, 456, 999],
            "controllers": "auto"
        },
        "charts": {
            "generate": True,
            "types": ["all"],
            "dpi": 300,
            "formats": ["png", "pdf"]
        },
        "parallel": {
            "enabled": True,
            "max_workers": 6
        }
    },
    
    "paper_medium": {
        "name": "論文中等強度實驗",
        "description": "總評估步數約1.6M，用於快速驗證和初步分析",
        "estimated_time": "4-6小時",
        "icon": "📊",
        "total_eval_steps": 1600000,
        "training": {
            "dqn_step": {"ticks": 1600000, "learning_rate": 0.0005, "batch_size": 64},
            "dqn_global": {"ticks": 1600000, "learning_rate": 0.0005, "batch_size": 64},
            
            "nerl_step_a": {"generations": 20, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_A},
            "nerl_global_a": {"generations": 20, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_A},

            "nerl_step_b": {"generations": 20, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_B},
            "nerl_global_b": {"generations": 20, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_B},
        },
        "evaluation": {
            "ticks": 20000,
            "repeats": 10,
            "controllers": "auto"
        },
        "charts": {
            "generate": True,
            "types": ["all"],
            "dpi": 300,
            "formats": ["png", "pdf"]
        },
        "parallel": {
            "enabled": True,
            "strategy": "batch_execution",  # 分批執行策略
            "max_workers": 8
        }
    },
    
    "paper_high": {
        "name": "論文高強度實驗",
        "description": "總評估步數約3.2M，用於最終論文數據，追求模型極限效能",
        "estimated_time": "8-12小時",
        "icon": "🎯",
        "recommended": True,
        "total_eval_steps": 3200000,
        "training": {
            "dqn_step": {"ticks": 3200000, "learning_rate": 0.0005, "batch_size": 64},
            "dqn_global": {"ticks": 3200000, "learning_rate": 0.0005, "batch_size": 64},
            
            "nerl_step_a": {"generations": 40, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_A},
            "nerl_global_a": {"generations": 40, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_A},

            "nerl_step_b": {"generations": 40, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_B},
            "nerl_global_b": {"generations": 40, "population": 20, "eval_ticks": 4000, "parallel_workers": 4, **NERL_CONFIG_B},
        },
        "evaluation": {
            "ticks": 20000,
            "repeats": 15,
            "controllers": "auto"
        },
        "charts": {
            "generate": True,
            "types": ["all"],
            "dpi": 300,
            "formats": ["png", "pdf"]
        },
        "parallel": {
            "enabled": True,
            "strategy": "batch_execution",  # 分批執行策略
            "max_workers": 8
        }
    }
}

# 支援的控制器類型
AVAILABLE_CONTROLLERS = {
    "traditional": ["time_based", "queue_based"],
    "ai": ["dqn_step", "dqn_global", "nerl_step", "nerl_global"],
    "nerl_variants": ["nerl_step_a", "nerl_global_a", "nerl_step_b", "nerl_global_b"],
    "all": ["time_based", "queue_based", "dqn_step", "dqn_global", "nerl_step", "nerl_global", 
            "nerl_step_a", "nerl_global_a", "nerl_step_b", "nerl_global_b"]
}

# 圖表類型配置
CHART_TYPES = {
    "basic": ["performance_comparison", "algorithm_comparison"],
    "all": ["performance_comparison", "algorithm_comparison", "reward_comparison", 
            "performance_rankings", "comprehensive_heatmap"]
}

# 自定義參數範本
CUSTOM_PARAMETER_TEMPLATES = {
    "training": {
        "dqn": {
            "agent": "dqn",
            "reward_mode": ["step", "global"],
            "training_ticks": 10000,
            "learning_rate": 0.001,
            "batch_size": 32,
            "epsilon_start": 1.0,
            "epsilon_end": 0.01,
            "epsilon_decay": 0.995
        },
        "nerl": {
            "agent": "nerl",
            "reward_mode": ["step", "global"],
            "generations": 20,
            "population": 20,
            "eval_ticks": 2000,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "elite_size": 4
        }
    },
    "evaluation": {
        "controllers": "auto",
        "ticks": 15000,
        "repeats": 3,
        "seeds": [42, 123, 789],
        "description": "custom_experiment",
        "output_dir": None,
        "analysis_only": False
    },
    "charts": {
        "types": "all",
        "dpi": 300,
        "format": "png",
        "style": "whitegrid",
        "save_data": True
    }
}

def get_preset(preset_name: str) -> dict:
    """
    獲取指定的預設配置
    
    Args:
        preset_name: 預設配置名稱 ('quick', 'standard', 'complete')
    
    Returns:
        dict: 預設配置字典
    """
    if preset_name not in EXPERIMENT_PRESETS:
        raise ValueError(f"未知的預設配置: {preset_name}")
    
    return EXPERIMENT_PRESETS[preset_name].copy()

def list_presets() -> list:
    """
    列出所有可用的預設配置
    
    Returns:
        list: 預設配置列表
    """
    presets = []
    for key, config in EXPERIMENT_PRESETS.items():
        preset_info = {
            "key": key,
            "name": config["name"],
            "description": config["description"],
            "estimated_time": config["estimated_time"],
            "icon": config.get("icon", "🔸"),
            "recommended": config.get("recommended", False)
        }
        presets.append(preset_info)
    
    return presets

def get_controller_list(controller_type: str = "all") -> list:
    """
    獲取控制器列表
    
    Args:
        controller_type: 控制器類型 ('traditional', 'ai', 'all')
    
    Returns:
        list: 控制器名稱列表
    """
    if controller_type not in AVAILABLE_CONTROLLERS:
        controller_type = "all"
    
    return AVAILABLE_CONTROLLERS[controller_type].copy()

def get_custom_template(category: str, subcategory: str = None) -> dict:
    """
    獲取自定義參數範本
    
    Args:
        category: 參數類別 ('training', 'evaluation', 'charts')
        subcategory: 子類別 (僅用於 training: 'dqn', 'nerl')
    
    Returns:
        dict: 參數範本
    """
    if category not in CUSTOM_PARAMETER_TEMPLATES:
        raise ValueError(f"未知的參數類別: {category}")
    
    template = CUSTOM_PARAMETER_TEMPLATES[category]
    
    if subcategory and isinstance(template, dict) and subcategory in template:
        return template[subcategory].copy()
    
    return template.copy()

# 用於顯示的預設配置摘要
def format_preset_summary(preset_name: str) -> str:
    """
    格式化預設配置摘要用於顯示
    
    Args:
        preset_name: 預設配置名稱
    
    Returns:
        str: 格式化的摘要字串
    """
    preset = get_preset(preset_name)
    
    summary = f"{preset['icon']} {preset['name']} ({preset['estimated_time']})\n"
    
    # 檢查配置格式
    training = preset['training']
    if any('_' in task_name for task_name in training.keys()):
        # 新格式：論文級實驗
        dqn_tasks = [name for name in training.keys() if name.startswith('dqn_')]
        nerl_tasks = [name for name in training.keys() if name.startswith('nerl_')]
        
        summary += f"    - DQN: {len(dqn_tasks)} 個任務 "
        if dqn_tasks:
            sample_dqn = training[dqn_tasks[0]]
            # 檢查是否為字典類型
            if isinstance(sample_dqn, dict):
                ticks = sample_dqn.get('ticks', 'N/A')
                summary += f"({ticks} ticks 每個)\n"
            else:
                summary += f"({sample_dqn} ticks 每個)\n"
        else:
            summary += "\n"
            
        summary += f"    - NERL: {len(nerl_tasks)} 個任務 "
        if nerl_tasks:
            sample_nerl = training[nerl_tasks[0]]
            # 檢查是否為字典類型
            if isinstance(sample_nerl, dict):
                generations = sample_nerl.get('generations', 'N/A')
                population = sample_nerl.get('population', 'N/A')
                summary += f"({generations}代, {population}個體)\n"
            else:
                summary += f"({sample_nerl})\n"
        else:
            summary += "\n"
            
        # 顯示總評估步數
        if 'total_eval_steps' in preset:
            steps = preset['total_eval_steps']
            summary += f"    - 總訓練量: {steps:,} 步 ({steps/1e6:.1f}M)\n"
    else:
        # 舊格式
        summary += f"    - DQN: {training.get('dqn_ticks', 'N/A')} ticks\n"
        summary += f"    - NERL: {training.get('nerl_generations', 'N/A')}代, "
        summary += f"{training.get('nerl_population', 'N/A')}個體, "
        summary += f"{training.get('nerl_eval_ticks', 'N/A')} eval ticks\n"
    
    # 評估配置
    if 'evaluation' in preset:
        evaluation = preset['evaluation']
        summary += f"    - 評估: {evaluation.get('ticks', 'N/A')} ticks × "
        summary += f"{evaluation.get('repeats', 'N/A')}次\n"
    
    summary += f"    - 適合：{preset['description']}"
    
    if preset.get('recommended'):
        summary += " [推薦]"
    
    return summary