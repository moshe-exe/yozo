import json
import requests
import os


def get_telegram_text(event):
    if 'body' not in event:
        return None, "No message body"

    event_body = json.loads(event.get('body'))

    if 'message' not in event_body:
        return None, "No message"

    if 'text' not in event_body['message']:
        return None, "No message text"

    return event_body['message']['text'], None


def lambda_handler(event, context):
    msg_text, error = get_telegram_text(event)

    if error:
        msg_text = f"Error: {error}"

    chat_id = os.environ['CHANNEL_ID']
    telegram_token = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{telegram_token}/"

    params = {'chat_id': chat_id, 'text': msg_text}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
