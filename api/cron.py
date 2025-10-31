from http.server import BaseHTTPRequestHandler
import os
import linebot.v3.messaging
import requests
import re
import json
import html
import redis
import argparse
import tweepy
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

configuration = linebot.v3.messaging.Configuration(
    access_token = os.environ['LINE_TOKEN']
)

redis_client = redis.from_url(os.environ['REDIS_URL'])

x_client = tweepy.Client(
    consumer_key=os.environ['X_CONSUMER_KEY'],
    consumer_secret=os.environ['X_CONSUMER_SECRET'],
    access_token=os.environ['X_TOKEN'],
    access_token_secret=os.environ['X_SECRET']
)

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
        try:
            api_instance.push_message(push_message_request)
        except linebot.v3.messaging.exceptions.ApiException as api_exception:
            reason = api_exception.reason
            message = json.loads(api_exception.body)["message"] if api_exception.body else ''
            print(f'Push Failed: {reason}: {message}')

def x_post_message(message):
    x_client.create_tweet(text=message)

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
    return '\n'.join([f'{d["title"]} ({d["new_posts"]})' for d in deltas_trimmed])

def run_pipeline(threshold):
    # Load new/old threads and compute deltas
    new_threads = fetch_subback()
    old_threads = json.loads(redis_client.get('dumps').decode('utf-8'))
    deltas = compute_deltas(old_threads, new_threads)

    # Abort if total new posts is under threshold
    total = sum(d['new_posts'] for d in deltas)
    if total < threshold:
        print(f'Abort: Total={total}')
        return

    # Save theads for next comparison
    redis_payload = json.dumps(new_threads, ensure_ascii=False)
    redis_client.set('dumps', redis_payload)

    # Send top 10 as message and save to redis
    deltas_sorted = sorted(deltas, key=lambda x: x['new_posts'], reverse=True)
    message = deltas_to_message(deltas_sorted)
    # line_push_message(message if message else 'Pipeline produced empty messsage.')
    x_post_message(message if message else 'Pipeline produced empty messsage.')
    top_ten = json.dumps(deltas_sorted[:10], ensure_ascii=False)
    redis_client.set('top_ten', top_ten)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        run_pipeline(0)
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("threshold", type=int, help="threshold for push")
    args = parser.parse_args()
    run_pipeline(args.threshold)
