import requests
import os
import json
import time
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

# 

if __name__ == "__main__":
    date_time_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    msg = f"{date_time_str} 发送成功"
    send_feishu_text("测试一下", msg)