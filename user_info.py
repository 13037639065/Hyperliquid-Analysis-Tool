import json
from hyperliquid.info import Info
from hyperliquid.utils import constants

ADDRESS = "xxx"

if __name__ == "__main__":
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    user_info = info.user_state(ADDRESS)
    print(json.dumps(user_info, indent=4))  