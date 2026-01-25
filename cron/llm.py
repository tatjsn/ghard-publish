import os
from textwrap import dedent
from google import genai
from google.genai import types

SUMMARY_PROMPT = dedent("""
以下の JSON 配列には掲示板スレッドタイトルが入っています。
タイトルを圧縮して、全角「／」でつなぎ、1つのテキストにしてください。
圧縮ルール：
- 冗長表現や装飾は削除
- スレ番号不要
- 簡潔に表現
- NSFWはYahoo!トピック程度に安全化
- 情報は可能な限り維持

JSONやリスト形式で返さず、**必ず文字列だけ**で出力すること。

JSON データ：
{input_json}
""")

def generate_summary(titles_json):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
    prompt = SUMMARY_PROMPT.format(input_json=titles_json)
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
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
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text
