# util functions for Hyperliquid analysis tool
import os
import __main__

def hyper_file_log(message):
    base_path = "trading_data_cache/logs"
    """
    将日志信息追加写入指定文件
    
    参数:
        message (str): 要写入的信息
        path (str): 日志文件路径，默认为 hyer_log.txt
    """
    os.makedirs(base_path, exist_ok=True)
    pid = os.getpid()
    procoss_name = os.path.basename(__main__.__file__).replace(".py", "")  # 获取主进程文件名
    with open(os.path.join(base_path, f"{procoss_name}_{pid}.log"), "a", encoding="utf-8") as f:
        f.write(f"{message}\n")