import json
import requests
import os
import boto3

queue_url = os.environ['QUEUE_URL']
sqs = boto3.client('sqs')


def wrap_message(message):
    try:
        wrapped_message = {
            "sender": message.get('from').get('first_name'),
            "text": message.get('text'),
            "chat_id": message.get('chat').get('id'),
            "message_id": message.get('message_id')
        }
        return wrapped_message

    except Exception as e:
        return str(e)


def get_message(event):
    if 'body' not in event:
        return "No body in event"

    event_body = json.loads(event.get('body'))

    if 'message' not in event_body:
        return "No message in body"

    return wrap_message(event_body['message'])


def push_to_queue(message):
    if not queue_url:
        return "No queue url found in environment"

    try:
        msg_dedup_id = f"{message['chat_id']}/{message['message_id']}"
        response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message),
                MessageGroupId='DT2_MESSAGES',
                MessageDeduplicationId=msg_dedup_id
            )
        return response
    except Exception as e:
        return str(e)


def get_aprox_queue_size():
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        approximate_num_messages = int(
            response['Attributes']['ApproximateNumberOfMessages']
            )
        return approximate_num_messages
    except Exception as e:
        return str(e)


def lambda_handler(event, context):
    processed_msg = get_message(event)
    queue_response = push_to_queue(processed_msg)
    aprox_queue_size = get_aprox_queue_size()

    debug_dict = {
        'queue_msg': processed_msg,
        'queue_response': queue_response,
        'aprox_queue_size': aprox_queue_size
    }

    chat_id = os.environ['CHANNEL_ID']
    telegram_token = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{telegram_token}/"

    pretty_debug_str = json.dumps(debug_dict, indent=4)
    params = {'chat_id': chat_id, 'text': pretty_debug_str}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
