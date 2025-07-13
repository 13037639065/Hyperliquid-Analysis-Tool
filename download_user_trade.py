import csv
import os
import time
from datetime import datetime
from hyperliquid.info import Info
from hyperliquid.utils import constants
import argparse

INFO = Info(constants.MAINNET_API_URL, skip_ws=True)
OUTPUT_DIR = "trading_data_cache/user_fills"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_new_filename(address):
    now_str = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
    return os.path.join(OUTPUT_DIR, f"{address[-8:]}_{now_str}.csv")

def open_new_file(address):
    filename = get_new_filename(address)
    f = open(filename, "w", newline="")
    headers = ['coin', 'px', 'sz', 'side', 'time', 'startPosition', 'dir', 'closedPnl', 'hash', 'oid', 'crossed','fee','tid', 'cloid','feeToken']
    writer =  csv.DictWriter(f,  fieldnames=headers)
    return f, writer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download user trade data from Hyperliquid")
    parser.add_argument('--user', '-u', required=True, type=str, help='User address')
    args = parser.parse_args()

    user_address = args.user
    writer=None
    f = None

    try:
        pre_hash = []
        while True:
            try:
                fills = INFO.user_fills(user_address)
            except Exception as e:
                print(e)
                time.sleep(1)
                continue

            if len(fills) == 0:
                time.sleep(1)
                continue
                
            # 由于最新的在前面 所以翻转数组
            fills = fills[::-1]

            print(datetime.now())
            if fills[0]["hash"] not in pre_hash:
                if f is not None:
                    f.close()
                f, writer = open_new_file(user_address)
                writer.writeheader()
                for fill in fills:
                    writer.writerow(fill)
            else:
                for fill in fills:
                    oid = fill["hash"]
                    if oid in pre_hash:
                        continue

                    writer.writerow(fill)
                    f.flush()  # 实时写入

            time.sleep(1)
            pre_hash = [fill['hash'] for fill in fills]

    except KeyboardInterrupt:
        print("[INFO] Interrupted. Closing file.")
        f.close()
