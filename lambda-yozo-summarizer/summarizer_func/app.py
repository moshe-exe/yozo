import json
import requests
import os


def lambda_handler(event, context):
    telegram_msg = event.get('message').get('text')
    chat_id = os.environ['CHANNEL_ID']
    telegram_token = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{telegram_token}/"

    params = {'chat_id': chat_id, 'text': telegram_msg}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
