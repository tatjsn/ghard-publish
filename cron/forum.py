import os
import re
import html
import requests

line_pattern = re.compile(r'^<a href="([^/]+)/[^"]*">\d+: (.+) \((\d+)\)</a>')

def fetch_subback():
    data_url = os.environ['SUBBACK_URL']
    res = requests.get(data_url)
    return extract_threads(res.text)

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
