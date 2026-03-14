import re
import enchant

# Initialize English dictionary
english_dict = enchant.Dict("en_US")

def english_ratio(text: str) -> float:
    # Extract words (ignore punctuation and numbers)
    words = re.findall(r"[a-zA-Z]+", text)

    if not words:
        return 0.0

    english_count = sum(1 for w in words if english_dict.check(w))

    return english_count / len(words)
