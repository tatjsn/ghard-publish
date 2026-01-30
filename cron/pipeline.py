from http.server import BaseHTTPRequestHandler
import os
import json
import redis
import argparse
from dotenv import load_dotenv
from twitter import post_message
from llm import generate_summary
from forum import fetch_subback, compute_deltas, deltas_to_message

if __name__ == '__main__':
    load_dotenv()

redis_client = redis.from_url(os.environ['REDIS_URL'])

def process_thread_deltas(threshold):
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
    redis_client.set('legacy_message', message if message else 'Pipeline produced empty messsage.')

    top_ten = json.dumps(deltas_sorted[:10], ensure_ascii=False)
    redis_client.set('top_ten', top_ten)

    titles = json.dumps([item["title"] for item in deltas_sorted[:10]])
    summary = generate_summary(titles)
    post_message(summary)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("threshold", type=int, help="threshold for push")
    args = parser.parse_args()
    process_thread_deltas(args.threshold)
