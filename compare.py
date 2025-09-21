import re
import os
import json
import html
from google import genai
from google.genai import types


def generate(ndjson_string):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"""
                <context>
                You are given a delta of forum threads as NDJSON embedded directly below.
                Each line is a thread object:

                {{"title": "Thread Title", "new_posts": N}}

                - `new_posts` = number of posts added since yesterday

                NDJSON data starts below:
                {ndjson_string}
                </context>

                Write 5 paragraphs summarizing what is happening that is worth reporting as news, ordered by popularity.
                Use podcast style Japanese that is suitable for text-to-speech.
                Focus on speed; do not spend extra effort analyzing. Keep it quick as possible.
                """),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
        tools=tools,
    )

    print("Waiting...")
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="", flush=True)

line_pattern = re.compile(r'^<a href="([^/]+)/[^"]*">\d+: (.+) \((\d+)\)</a>')

def extract_threads(file_path):
    threads = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            m = line_pattern.match(line)
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

if __name__ == '__main__':
    old_threads = extract_threads('./subback-old.html')
    new_threads = extract_threads('./subback-new.html')
    deltas = compute_deltas(old_threads, new_threads)
    deltas_sorted = sorted(deltas, key=lambda x: x["new_posts"], reverse=True)[:100]
    ndjson_string = '\n'.join([json.dumps(d, ensure_ascii=False) for d in deltas_sorted])
    print(html.unescape(ndjson_string))
    generate(html.unescape(ndjson_string))
