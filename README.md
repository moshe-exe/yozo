Video on how to develop lambda from vscode

https://www.youtube.com/watch?v=DA3hlLxTl-8

install AWS Toolkit
install SAM CLI

- brew install sam and six

command: `sam deploy --guided --profile personal`

change tamplate for api gateway, method:post and route:summary

change function folder name and also handler in template

sam deploy

change resource name and outputs names

sam deploy

telegram create bot
telegram create chat group
telegram create channel
invite bot as admin in both

set up envs
secrets with aws secret manager
and not secrets with only template

aws secretsmanager create-secret --profile personal --name yozo-my-bot-token --secret-string "VALUE" --region us-east-1
aws secretsmanager create-secret --profile personal --name yozo-my-channel-id --secret-string "VALUE" --region us-east-1
aws secretsmanager create-secret --profile personal --name yozo-my-group-id --secret-string "VALUE" --region us-east-1

add telegram send message integration:

```python
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
```

deploy and test

now set webhook so telegram can trigger this lambda event

```bash
curl https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$WEBHOOK_URL
```

## Sync live

sam sync --stack-name yozo-chat --watch --profile personal --region us-east-1
