import tweepy
import os
import unicodedata

def post_message(message):
    client = tweepy.Client(
        consumer_key=os.environ['X_CONSUMER_KEY'],
        consumer_secret=os.environ['X_CONSUMER_SECRET'],
        access_token=os.environ['X_TOKEN'],
        access_token_secret=os.environ['X_SECRET']
    )

    post_with_retry(client, message, 280, 3)

def post_with_retry(client, message, limit, retry):
    # stop conditions
    if retry < 0 or limit <= 0:
        print("Skip posting: retry < 0 or limit <= 0")
        return

    try:
        chunks = split_by_weight(message, limit)
        chunk_wls = [weight_length(chunk) for chunk in chunks]
        print(f'Posting {chunk_wls}')

        reply_to = None
        for chunk in chunks:
            tweet = client.create_tweet(
                text=chunk,
                in_reply_to_tweet_id=reply_to
            )
            reply_to = tweet.data["id"]

    except Exception as e:
        print(f"Error while posting (limit={limit}, retry={retry}): {e}")
        # recursively retry with smaller limit
        post_with_retry(
            client=client,
            message=message,
            limit=limit - 4,
            retry=retry - 1
        )


def split_by_weight(s: str, max_weight: int) -> list[str]:
    result = []
    current = ""

    for ch in s:
        candidate = current + ch
        if weight_length(candidate) <= max_weight:
            current = candidate
        else:
            if current:
                result.append(current)
            current = ch

            # Optional safety: if a single char exceeds limit
            if weight_length(current) > max_weight:
                raise ValueError(f"Single character '{ch}' exceeds max_weight")

    if current:
        result.append(current)

    return result



def weight_length(text: str) -> int:
    """
    Limited X-style character counter:
      - Normalize text to Unicode NFC
      - CJK characters count as 2
      - All other characters count as 1
      - No URL shortening
      - No emoji special handling
    """
    text = unicodedata.normalize("NFC", text)
    count = 0

    for ch in text:
        if (
            "\u4E00" <= ch <= "\u9FFF" or  # CJK Unified Ideographs
            "\u3400" <= ch <= "\u4DBF" or  # CJK Extension A
            "\u3040" <= ch <= "\u30FF" or  # Hiragana & Katakana
            "\uAC00" <= ch <= "\uD7AF"     # Hangul Syllables
        ):
            count += 2
        else:
            count += 1

    return count
