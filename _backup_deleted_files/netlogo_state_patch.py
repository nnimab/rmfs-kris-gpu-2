"""
Monkey patch for netlogo.py to use unique state files
在 evaluate.py 開頭 import 這個檔案即可
"""
import os
import netlogo

# 保存原始函數
_original_setup = netlogo.setup
_original_tick = netlogo.tick

def get_unique_state_file():
    """生成唯一的狀態檔案名稱"""
    sim_id = os.environ.get('SIMULATION_ID', '')
    if sim_id:
        return f'netlogo_{sim_id}.state'
    # 使用進程ID作為備案
    return f'netlogo_{os.getpid()}.state'

# 替換 'netlogo.state' 字串的函數
def patch_state_filename(original_func):
    """修改函數中的 netlogo.state 為唯一檔名"""
    import inspect
    import types
    
    # 獲取函數原始碼
    source = inspect.getsource(original_func)
    
    # 替換檔名
    state_file = get_unique_state_file()
    source = source.replace("'netlogo.state'", f"'{state_file}'")
    source = source.replace('"netlogo.state"', f'"{state_file}"')
    
    # 編譯新函數
    exec_globals = original_func.__globals__.copy()
    exec(source, exec_globals)
    
    # 返回新函數
    func_name = original_func.__name__
    return exec_globals[func_name]

# Monkey patch
print(f"Patching netlogo.py to use unique state files...")
netlogo.setup = patch_state_filename(_original_setup)
netlogo.tick = patch_state_filename(_original_tick)

# 同樣處理其他需要的函數
if hasattr(netlogo, 'set_traffic_controller'):
    netlogo.set_traffic_controller = patch_state_filename(netlogo.set_traffic_controller)

print(f"Patched! State file will be: {get_unique_state_file()}")