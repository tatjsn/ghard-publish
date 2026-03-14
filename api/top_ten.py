from http.server import BaseHTTPRequestHandler
import os   
import json
import redis
import time
import re
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

redis_client = redis.from_url(os.environ['REDIS_URL'])

def render():
    unix_time, total, threshold = map(int, redis_client.get('status').decode('utf-8').split(','))
    unix_time_dump, total_dump = map(int, redis_client.get('deltas_status').decode('utf-8').split(','))
    deltas_sorted = json.loads(redis_client.get('deltas_sorted').decode('utf-8'))
    now_time = int(time.time())
    delta_time_m = (now_time - unix_time) // 60
    delta_time_dump_m = (now_time - unix_time_dump) // 60

    pattern = re.compile(r'■■速報＠ゲーハー板')
    matched_new_posts = sum(d["new_posts"] for d in deltas_sorted if pattern.search(d["title"]))
    matched_percent = (matched_new_posts / total_dump * 100) if total_dump else 0

    return '<body>' + \
        f'<p>Last crawl: {delta_time_m} minutes ago' + \
        f'<p><label>Threshold: <progress value="{total}" max="{threshold}">{total}/{threshold}</progress></label>' + \
        f'<p>Last dump: {delta_time_dump_m} minutes ago, {total_dump} posts' + \
        f'<p><label>Sokuho {matched_percent:.2f}%: <progress value="{matched_new_posts}" max="{total_dump}">{matched_new_posts}/{total_dump}</progress></label>' + \
        ''.join([f'<p>{d["title"]} ({d["new_posts"]})' for d in deltas_sorted[:10]])


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
