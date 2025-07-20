import torch

_device = None

def get_device():
    """
    檢查是否有可用的 CUDA GPU，並返回相應的 torch.device。
    使用緩存機制避免重複打印信息。
    """
    global _device
    if _device is None:
        if torch.cuda.is_available():
            print("INFO: CUDA is available. Using GPU.")
            _device = torch.device("cuda")
        else:
            print("INFO: CUDA not available. Using CPU.")
            _device = torch.device("cpu")
    return _device 