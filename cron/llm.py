import os
from textwrap import dedent
from google import genai
from google.genai import types

SUMMARY_PROMPT = dedent("""
あなたはYahoo!トピックス編集部の編集者です。
以下に掲示板スレッドタイトルの JSON 配列を渡します。

編集方針：
- 各タイトルを、Yahoo!トピックスに掲載される見出しとして適切な表現に言い換える
- 扇情的・感情的・攻撃的・過激な表現は中立的かつ穏当な表現に修正する
- 俗語、ネットスラング、煽り、誇張、装飾記号は除去する
- スレッド番号やIDなど編集上不要な情報は削除する
- 性的・暴力的・差別的表現は、Yahoo!トピックスの倫理基準に沿って言い換える
- 雑談所的なシリーズものは掲載対象外として省く
- **見出しでは句読点（「。」「、」）を使用しない**
- 見出しは体言止めまたは簡潔な名詞句を基本とする

出力ルール：
- 採用した見出しのみを、全角「／」で連結する
- 出力は1行のテキストのみとする
- JSON、配列、箇条書き、説明文、前置きは一切含めない

入力：
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
