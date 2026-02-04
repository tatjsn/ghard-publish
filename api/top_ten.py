from http.server import BaseHTTPRequestHandler
import os   
import json
import redis
import time
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

redis_client = redis.from_url(os.environ['REDIS_URL'])

def render():
    unix_time, total, threshold = map(int, redis_client.get('status').decode('utf-8').split(','))
    top_ten = json.loads(redis_client.get('top_ten').decode('utf-8'))
    now_time = int(time.time())
    delta_time_m = (now_time - unix_time) // 60
    return '<body>' + \
        f'<p>Last update: {delta_time_m} minutes ago' + \
        f'<p><label>Progress: <progress value="{total}" max="{threshold}">{total}/{threshold}</progress></label>' + \
        ''.join([f'<p>{d["title"]} ({d["new_posts"]})' for d in top_ten])


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = render().encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type','text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(payload)
        return

if __name__ == '__main__':
    print(render())
