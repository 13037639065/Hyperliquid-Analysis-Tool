# util functions for Hyperliquid analysis tool

def hyper_file_log(message, path="trading_data_cache/hyer_log.txt"):
    """
    将日志信息追加写入指定文件
    
    参数:
        message (str): 要写入的信息
        path (str): 日志文件路径，默认为 hyer_log.txt
    """
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")