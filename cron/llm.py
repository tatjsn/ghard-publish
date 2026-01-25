import os
from google import genai
from google.genai import types

def generate_summary(deltas_json):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"""
                You are given a JSON array of objects. Each object has:
                - "title": forum thread title
                - "new_posts": number of new posts in the last hour

                Using ONLY information from the thread titles and their posting volume, extract the underlying hot topics of the past hour. Merge related threads into single topics where appropriate.

                Output a Japanese summary in the following style:

                - Each topic must be exactly: [Noun][4-character compressed kanji phrase]
                  - Noun = main topic
                  - 4-character compressed kanji phrase = a pseudo-idiom invented from title wording only that expresses the angle or sentiment
                - No spaces between noun and 4-character phrase.
                - Separate multiple topics with "／".
                - No verbs, no preface, no narrative, no filler.
                - Do NOT quote or paraphrase thread titles literally.
                - Do NOT infer sentiment from imagined posts; only use what is suggested by titles.
                - Weight topics by higher "new_posts".
                - Reduce or ignore recurring/series threads.

                Length constraints:
                - Target: 120-130 Japanese characters.
                - Hard limit: under 140 Japanese characters (Twitter/X free tier).

                Input:
                {deltas_json}"""),
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

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text
