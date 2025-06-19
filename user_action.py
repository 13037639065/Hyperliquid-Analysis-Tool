import argparse
import time
import json
from hyperliquid.info import Info
from hyperliquid.utils  import constants 


# Initialize info object
info = Info(constants.MAINNET_API_URL, skip_ws=True)


def monitor_positions(token):
    """Monitor positions for specified token and detect changes"""
    # Get all addresses from file
    with open('./trading_data_cache/result.txt', 'r') as f:
        addresses = [line.strip() for line in f.readlines()]

    previous_positions = {}

    while True:
        current_positions = {}
        

        # Check for each address
        for address in addresses:
            try:
                # Get user's fills and positions
                positions = info.user_state(address)
                
                # Get current position for token
                asset_positions = positions.get('assetPositions', [])
                token_position = next((p for p in asset_positions if p['position']['coin'] == token), None)

                # Store current position
                current_positions[address] = {
                    'position': token_position,
                }

                # Check for position changes
                if address in previous_positions:
                    prev_pos = previous_positions[address]['position']
                    curr_pos = token_position
                    
                    
                    # Detect position changes
                    if prev_pos is None and curr_pos is not None:
                        print(f"[开仓] {address} 开始持有 {token}")
                    elif prev_pos is not None and curr_pos is None:
                        print(f"[平仓] {address} 结束了 {token} 持仓")
                    elif prev_pos and curr_pos:
                        # Get position size with safety checks
                        prev_size_str = prev_pos['position'].get('szi', '0') if prev_pos and 'position' in prev_pos else '0'
                        curr_size_str = curr_pos['position'].get('szi', '0') if curr_pos and 'position' in curr_pos else '0'
                        
                        try:
                            prev_size = float(prev_size_str)
                            curr_size = float(curr_size_str)
                            
                            # Detect position size change
                            if abs(curr_size) > abs(prev_size):
                                direction = "加仓" if (curr_size > 0 and curr_size > prev_size) or (curr_size < 0 and curr_size < prev_size) else "减仓"
                                print(f"[{direction}] {address} 在 {token} 上调整仓位: {prev_size} -> {curr_size}")
                            
                            # Detect position reversal
                            if prev_size * curr_size < 0:
                                new_direction = "做多" if curr_size > 0 else "做空"
                                print(f"[反手] {address} 在 {token} 转向 {new_direction}")

                        except ValueError:
                            print(f"Error converting position size to float for {address} {token}")
                            continue

                
            except Exception as e:
                print(f"Error processing {address}: {str(e)}")
                continue

        
        # Update previous positions
        previous_positions = current_positions
        
        
        # Wait before next check (e.g., 5 seconds)
        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='实时监控Hyperliquid用户持仓')
    parser.add_argument('--symbol', '-s', type=str, required=True, choices=['BTC', 'ETH', 'SOL'],
                        help='要监控的代币 (BTC or ETH)')
    args = parser.parse_args()
    
    print(f"开始实时监控 {args.symbol} 持仓...")
    monitor_positions(args.symbol)