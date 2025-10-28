from http.server import BaseHTTPRequestHandler
import os   
import json
import redis
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

redis_client = redis.from_url(os.environ['REDIS_URL'])

def render():
    top_ten = json.loads(redis_client.get('top_ten').decode('utf-8'))
    return '<body>' + ''.join([f'<p>{d["title"]} ({d["new_posts"]})' for d in top_ten])


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = render().encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(payload)
        return

if __name__ == '__main__':
    print(render())
