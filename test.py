import json

# json load filename to dict
def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    
exchange_info = load_json("xxx.json")
symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == "BTCUSDC"), None)
if not symbol_info:
    print(f"Symbol BTCUSDC not found in exchange info")
else:
    print(f"Symbol BTCUSDC found in exchange info")