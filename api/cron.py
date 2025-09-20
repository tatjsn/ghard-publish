from http.server import BaseHTTPRequestHandler
import os
import linebot.v3.messaging

configuration = linebot.v3.messaging.Configuration(
    access_token = os.environ['LINE_TOKEN']
)

def line_push_message(message):
    with linebot.v3.messaging.ApiClient(configuration) as api_client:
        api_instance = linebot.v3.messaging.MessagingApi(api_client)
        push_message_request = linebot.v3.messaging.PushMessageRequest(
            to=os.environ.get('LINE_USER_ID'),
            messages=[linebot.v3.messaging.TextMessage(text=message)]
        )
        api_instance.push_message(push_message_request)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        line_push_message('Hello from handler')
        return

if __name__ == '__main__':
    line_push_message('Hello from main')
