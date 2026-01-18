import unicodedata

def count_x_characters_limited(text: str) -> int:
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
