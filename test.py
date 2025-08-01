import requests

def get_addresses_under_1btc():
    url = "https://api.blockchair.com/bitcoin/addresses?q=balance_usd(<30000)"  # 近似小于1BTC
    response = requests.get(url)
    data = response.json()
    for addr in data['data']:
        print(addr['address'], addr['balance'])

get_addresses_under_1btc()