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
