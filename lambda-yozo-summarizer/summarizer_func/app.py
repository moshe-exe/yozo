import json
import requests
import os
import boto3

QUEUE_URL = os.environ['QUEUE_URL']
GROUP_ID = os.environ['GROUP_ID']
BATCH_SIZE = 8  # int(os.environ['BATCH_SIZE'])
BATCH_SIZE_ITER = 8
sqs = boto3.client('sqs')

MODEL_ID = 'cohere.command-text-v14'
ACCEPT = 'application/json'
CONTENT_TYPE = 'application/json'
bedrock = boto3.client('bedrock-runtime')


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
        return httpStatusCode
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


def bedrock_inference(prompt):
    try:
        body = json.dumps({
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.2,
            "p": 0.99,
            "k": 0,
            "return_likelihoods": "NONE"
        })

        response = bedrock.invoke_model(
            body=body,
            modelId=MODEL_ID,
            accept=ACCEPT,
            contentType=CONTENT_TYPE
            )

        response_body = json.loads(response.get('body').read())
        return response_body.get('generations')[0].get('text')

    except Exception as e:
        return "Error: " + str(e)


def bedrock_summarize_chat(conversation):
    prompt = f"""
        Write a summary of this chat conversation.
Each message has the following structure "SENDER: MESSAGE_CONTENT".
Write 50 words or less. Write your summary in spanish.
```
{conversation}
```
    """
    return bedrock_inference(prompt)


def summarize_batch():
    try:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            AttributeNames=['All'],
            MaxNumberOfMessages=BATCH_SIZE_ITER + 1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=40,
            WaitTimeSeconds=0
        )

        if 'Messages' not in response:
            return f"No messages received. Response: {response}"

        conversation = ""
        for message in response['Messages']:
            tel_msg = json.loads(message['Body'])
            _ = tel_msg['message_id']
            sender = tel_msg['sender']
            text = tel_msg['text']
            conversation += f"{sender}: {text}\n"

            bedrock_summary = bedrock_summarize_chat(conversation)
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )

        return bedrock_summary, conversation

    except Exception as e:
        return "Error: " + str(e)


def lambda_handler(event, context):
    aprox_queue_size = get_aprox_queue_size()
    new_message = get_message(event)
    push_q_response = push_to_queue(new_message)

    telegram_response = ""
    pretty_debug_str = json.dumps({
        'aprox_queue_size': aprox_queue_size,
        'new_message': new_message,
        'push_queue_status': push_q_response,
    }, indent=4)

    CHAT_ID = os.environ['CHANNEL_ID']
    TELEGRAM_TOKEN = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"

    params = {'chat_id': CHAT_ID, 'text': pretty_debug_str}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    if aprox_queue_size >= BATCH_SIZE:
        summary, conversation = summarize_batch()
        telegram_response = f"SUM: {summary}" + "\n"

    CHAT_ID = os.environ['CHANNEL_ID']
    TELEGRAM_TOKEN = os.environ['BOT_TOKEN']

    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"

    params = {'chat_id': CHAT_ID, 'text': telegram_response}
    res = requests.post(f"{api_url}sendMessage", data=params).json()

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
