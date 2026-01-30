import linebot.v3.messaging
import os
import json

def push_message(message):
    configuration = linebot.v3.messaging.Configuration(
        access_token = os.environ['LINE_TOKEN']
    )
    with linebot.v3.messaging.ApiClient(configuration) as api_client:
        api_instance = linebot.v3.messaging.MessagingApi(api_client)
        push_message_request = linebot.v3.messaging.PushMessageRequest(
            to=os.environ.get('LINE_USER_ID'),
            messages=[linebot.v3.messaging.TextMessage(text=message)]
        )
        try:
            api_instance.push_message(push_message_request)
        except linebot.v3.messaging.exceptions.ApiException as api_exception:
            reason = api_exception.reason
            message = json.loads(api_exception.body)["message"] if api_exception.body else ''
            print(f'Push Failed: {reason}: {message}')
