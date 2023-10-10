import json
import requests
import os
import boto3

QUEUE_URL = os.environ['QUEUE_URL']
GROUP_ID = os.environ['GROUP_ID']
sqs = boto3.client('sqs')
BATCH_SIZE = 5  # int(os.environ['BATCH_SIZE'])
BATCH_SIZE_ITER = 5


def wrap_message(message):
    try:
        wrapped_message = {
            "message_id": message.get('message_id'),
            "sender": message.get('from').get('first_name'),
            "text": message.get('text'),
            # "chat_id": message.get('chat').get('id'),
        }
        return wrapped_message

    except Exception as e:
        return "Error: " + str(e)


def get_message(event):
    if 'body' not in event:
        return "No body in event"

    event_body = json.loads(event.get('body'))

    if 'message' not in event_body:
        return "No message in body"

    return wrap_message(event_body['message'])


def push_to_queue(message):
    if not QUEUE_URL:
        return "No queue url found in environment"

    try:
        msg_dedup_id = f"{GROUP_ID}/{message['message_id']}"
        response = sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(message),
                MessageGroupId='DT2_MESSAGES',
                MessageDeduplicationId=msg_dedup_id
            )
        httpStatusCode = response['ResponseMetadata']['HTTPStatusCode']
        return {'HTTPStatusCode': httpStatusCode}
    except Exception as e:
        return "Error: " + str(e)


def get_aprox_queue_size():
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        approximate_num_messages = int(
            response['Attributes']['ApproximateNumberOfMessages']
            )
        return approximate_num_messages
    except Exception as e:
        return "Error: " + str(e)


def summarize_batch():
    try:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            AttributeNames=['All'],
            MaxNumberOfMessages=BATCH_SIZE_ITER,
            MessageAttributeNames=['All'],
            VisibilityTimeout=20,
            WaitTimeSeconds=0
        )

        if 'Messages' not in response:
            return "No messages received."

        conversation = ""
        for message in response['Messages']:
            tel_msg = json.loads(message['Body'])
            id = tel_msg['message_id']
            sender = tel_msg['sender']
            text = tel_msg['text']
            conversation += f"({id}) {sender}: {text}\n"

            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )

        return conversation

    except Exception as e:
        return "Error: " + str(e)


def lambda_handler(event, context):
    processed_msg = get_message(event)
    queue_response = push_to_queue(processed_msg)
    aprox_queue_size = get_aprox_queue_size()

    debug_dict = {
        'queue_msg': processed_msg,
        'queue_response': queue_response,
        'aprox_queue_size': aprox_queue_size
    }

    if aprox_queue_size >= BATCH_SIZE:
        debug_dict['batch_summarize'] = summarize_batch()

    chat_id = os.environ['CHANNEL_ID']
    telegram_token = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{telegram_token}/"

    pretty_debug_str = json.dumps(debug_dict, indent=4)
    params = {'chat_id': chat_id, 'text': pretty_debug_str}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    if not res.get('ok'):
        params = {'chat_id': chat_id, 'text': json.dumps(res)}
        requests.post(f"{api_url}sendMessage", data=params).json()

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
