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


# twitter-text v3 parameters
SCALE = 100
DEFAULT_WEIGHT = 200

# Ranges taken directly from
# https://github.com/twitter/twitter-text/blob/master/config/v3.json
RANGES = [
    (0x0000, 0x10FF),   # includes basic Latin + many scripts
    (0x2000, 0x200D),
    (0x2010, 0x202F),
    (0x2050, 0x205F),
]

def weight_length(text: str) -> int:
    """
    Twitter-text v3–style weighted length counter:
      - NFC normalization
      - Characters in configured ranges count as 1
      - All others count as 2
      - No URL shortening
      - No extra emoji handling
    """
    text = unicodedata.normalize("NFC", text)
    total_weight = 0

    for ch in text:
        cp = ord(ch)
        weight = DEFAULT_WEIGHT

        for start, end in RANGES:
            if start <= cp <= end:
                weight = 100
                break

        total_weight += weight

    return total_weight // SCALE
