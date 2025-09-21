from http.server import BaseHTTPRequestHandler
import os
import linebot.v3.messaging
import requests
import re
import json
import html
import redis

configuration = linebot.v3.messaging.Configuration(
    access_token = os.environ['LINE_TOKEN']
)

redis_client = redis.from_url(os.environ['REDIS_URL'])

line_pattern = re.compile(r'^<a href="([^/]+)/[^"]*">\d+: (.+) \((\d+)\)</a>')

def extract_threads(blob):
    threads = []
    for line in blob.splitlines():
        m = line_pattern.match(html.unescape(line))
        if not m:
            continue
        thread_id, title, posts = m.groups()
        threads.append({
            "id": thread_id,
            "title": title.strip(),
            "posts": int(posts)
        })
    return threads

def fetch_subback():
    data_url = os.environ['SUBBACK_URL']
    res = requests.get(data_url)
    return extract_threads(res.text)

def line_push_message(message):
    with linebot.v3.messaging.ApiClient(configuration) as api_client:
        api_instance = linebot.v3.messaging.MessagingApi(api_client)
        push_message_request = linebot.v3.messaging.PushMessageRequest(
            to=os.environ.get('LINE_USER_ID'),
            messages=[linebot.v3.messaging.TextMessage(text=message)]
        )
        api_instance.push_message(push_message_request)

def compute_deltas(old_threads, new_threads):
    # Map by id for fast lookup
    old_map = {t["id"]: t for t in old_threads}
    new_map = {t["id"]: t for t in new_threads}

    deltas = []

    for thread_id, t_new in new_map.items():
        old_posts = old_map.get(thread_id, {}).get("posts", 0)
        delta = t_new["posts"] - old_posts
        if delta > 0:  # only keep threads that grew
            deltas.append({
                "title": t_new["title"],
                "new_posts": delta,
            })

    return deltas

def deltas_to_message(deltas):
    deltas_trimmed = deltas[:10]
    return '\n'.join([f'{d['title']} ({d['new_posts']})' for d in deltas_trimmed])

def run_pipeline():
    # Load new/old threads and compute deltas
    new_threads = fetch_subback()
    old_threads = json.loads(redis_client.get('dumps').decode('utf-8'))
    deltas = compute_deltas(old_threads, new_threads)

    # Save theads for next comparison
    redis_payload = json.dumps(new_threads, ensure_ascii=False)
    redis_client.set('dumps', redis_payload)

    # Send deltas as message
    deltas_sorted = sorted(deltas, key=lambda x: x['new_posts'], reverse=True)
    message = deltas_to_message(deltas_sorted)
    line_push_message(message if message else 'Pipeline produced empty messsage.')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        run_pipeline()
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return

if __name__ == '__main__':
    run_pipeline()
