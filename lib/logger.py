import logging
import sys
import os
from logging import Logger, FileHandler
from typing import Optional

# --- Color Codes for Terminal ---
# 全局變數來存儲當前 tick
_current_tick = None

def set_current_tick(tick):
    """設置當前 tick 以供日誌使用"""
    global _current_tick
    _current_tick = tick

def get_current_tick():
    """獲取當前 tick"""
    return _current_tick

class ColorFormatter(logging.Formatter):
    """A logging formatter that adds color to the output."""
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    
    # The format string now includes a placeholder for the tick
    BASE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: GREY + BASE_FORMAT + RESET,
        logging.INFO: GREY + BASE_FORMAT + RESET,
        logging.WARNING: YELLOW + BASE_FORMAT + RESET,
        logging.ERROR: RED + BASE_FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + BASE_FORMAT + RESET,
    }

    def format(self, record):
        # 如果消息中沒有 tick 信息且有全局 tick，自動添加
        tick = get_current_tick()
        if tick is not None and '[Tick' not in record.msg:
            record.msg = f"[Tick {tick}] {record.msg}"
        
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logger(name: str = "rmfs_logger", level: int = logging.INFO, log_file_path: Optional[str] = None) -> Logger:
    """
    Sets up a globally accessible logger with a specified name and level.
    
    This function configures a logger to output formatted and colored messages
    to the standard output, and optionally to a log file. It ensures that
    handlers are not added multiple times to the same logger.
    
    Args:
        name: The name for the logger. Defaults to "rmfs_logger".
        level: The logging level for the console (e.g., logging.INFO, logging.DEBUG). Defaults to logging.INFO.
        log_file_path: Optional path to a file where all logs (including DEBUG) will be written.
        
    Returns:
        The configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times, which would cause duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)  # Set logger to the lowest level to capture all messages
    
    # --- Console Handler (for user-facing progress) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)  # Console only shows INFO level and above
    console_handler.setFormatter(ColorFormatter())
    logger.addHandler(console_handler)
    
    # --- File Handler (for detailed debugging) ---
    if log_file_path:
        # 確保日誌目錄存在
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File captures everything
        # Use a non-colored formatter for the file
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Do not propagate messages to the root logger to avoid duplicate output
    logger.propagate = False
    
    return logger

def get_logger(name: str = "rmfs_logger", level: int = logging.INFO, log_file_path: Optional[str] = None) -> Logger:
    """
    Retrieves or initializes a logger instance by name.
    
    If the logger has not been configured yet, it will be initialized. 
    This is a convenience function to easily access the logger.
    
    Args:
        name: The name of the logger to retrieve. Defaults to "rmfs_logger".
        level: The logging level for the console. Defaults to logging.INFO.
        log_file_path: Optional path for the log file.
        
    Returns:
        The logger instance.
    """
    logger = logging.getLogger(name)
    # If the logger is not yet configured, or if we want to reconfigure it with a file path, set it up.
    # A simple check for handlers might not be enough if we want to add a file handler later.
    # Let's re-apply handlers if the file path is provided and wasn't there before.
    if log_file_path is not None:
        is_file_handler_present = any(isinstance(h, FileHandler) and h.baseFilename == os.path.abspath(log_file_path) for h in logger.handlers if isinstance(h, FileHandler))
    else:
        is_file_handler_present = False
    
    if not logger.hasHandlers() or (log_file_path and not is_file_handler_present):
        return setup_logger(name, level, log_file_path)
        
    return logger

# Example of how to use the logger:
if __name__ == "__main__":
    # Initialize the main logger for the application
    # It will log INFO to console and everything to 'app.log'
    logger = setup_logger(log_file_path='app.log')
    
    # --- Example Usage ---
    logger.debug("This is a debug message for detailed diagnostics (will only appear in app.log).")
    logger.info("This is an info message for general workflow (will appear in both console and app.log).")
    
    # You can include tick information directly in the message
    tick = 123
    set_current_tick(tick) # Set the global tick
    logger.info("A specific event happened at this tick.") # The tick will be added automatically
    set_current_tick(None) # Reset the global tick
    
    logger.warning("This is a warning message for potential issues.")
    logger.error("This is an error message for failures that occurred.")
    logger.critical("This is a critical message for severe errors.")
    
    # Example of a worker logger
    worker_logger = get_logger("worker1", log_file_path="worker1.log")
    worker_logger.info("This is a message from worker 1.")
    worker_logger.debug("This is a debug detail from worker 1.")
