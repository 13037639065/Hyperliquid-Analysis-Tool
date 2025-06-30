import requests
import os
import json

def send_feishu_text(title, content):
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "text",
        "content": content,
        "title": title,
    }
    print(f"[send_feishu_text]: \n{title}\n{content}")
    try:
        webhook_url = os.environ.get('WEBHOOK_URL')
        response = requests.post(webhook_url,  headers=headers, data=json.dumps(payload)) 
    except Exception as e:
        print(f"[send_feishu_text] error: {e}")