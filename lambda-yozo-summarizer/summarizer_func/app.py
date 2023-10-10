import json
import requests
import os


def wrap_message(message):
    DEBUG = True
    try:
        sender = message.get('from').get('first_name')
        text = message.get('text')
        chat_id = message.get('chat').get('id')
        message_id = message.get('message_id')
        wrapped_message = f"{sender}: {text}\n"
        if DEBUG:
            wrapped_message += f"CHAT_ID={chat_id} MSG_ID={message_id}"
        return wrapped_message, None

    except Exception as e:
        return None, str(e)


def get_message(event):
    if 'body' not in event:
        return None, "No message body"

    event_body = json.loads(event.get('body'))

    if 'message' not in event_body:
        return None, "No message"

    return wrap_message(event_body['message'])


def push_to_queue(msg, queue_url):
    if not queue_url:
        return None, "No queue url"

    return queue_url, None


def lambda_handler(event, context):
    msg_text, msg_error = get_message(event)
    queue_response, q_error = push_to_queue(msg_text, os.environ['QUEUE_URL'])

    if msg_error:
        msg_text = f"MESSAGE Error: {msg_error}"

    if q_error:
        msg_text = f"QUEUE Error: {q_error}"

    chat_id = os.environ['CHANNEL_ID']
    telegram_token = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{telegram_token}/"

    params = {'chat_id': chat_id, 'text': msg_text}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
