import re
import emoji

def clean_text_rule(text: str) -> str:
    """
    Applies the specified cleaning rules to a given text (post or comment).
    Returns the cleaned text, or an empty string if it fails validation.
    """
    if not text or not isinstance(text, str):
        return ""

    # Rule 3: Remove Links (http, https, www, embedded patterns)
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = re.sub(url_pattern, ' ', text)

    # Rule 5: Emoji Removal
    # emoji.replace_emoji completely strips emoji characters
    text = emoji.replace_emoji(text, replace='')

    # Rule 4: Special Character Filtering
    # Keep only Alphanumeric (including Ethiopic temporarily for check, though rule says no Amharic later), Spaces, and .,\'!?
    # We will remove characters that are NOT: Word characters (\w - includes unicode letters), whitespace (\s), or specific punctuation.
    # Note: \w includes numbers and underscores. We will specifically strip out underscores.
    
    # First, allow only specific punctuation
    allowed_chars = r'[^\w\s\.\,\'\"\?\!]'
    text = re.sub(allowed_chars, ' ', text)
    text = text.replace('_', ' ') # _ is in \w, so remove it explicitly

    # Normalize repeated punctuation marks
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\,+', ',', text)
    text = re.sub(r'\'+', '\'', text)
    text = re.sub(r'\"+', '\"', text)
    text = re.sub(r'\?+', '?', text)
    text = re.sub(r'\!+', '!', text)

    # Output Requirements: normalize spaces & trim
    text = re.sub(r'\s+', ' ', text).strip()

    # Apply validations that can reject the whole string
    
    # Rule 1: Minimum Word Requirement (at least 2 words)
    words = text.split()
    if len(words) < 2:
        return ""
        
    # Rule 2: Afaan Oromoo Language Constraint
    # - Must contain at least one Afaan Oromoo word (heuristic: we basically accept latin script but reject entirely if there's Arabic or Amharic)
    # - Must NOT contain Amharic (Ethiopic) script
    # - Must NOT contain Arabic script
    
    # Ethiopic Unicode Range: \u1200-\u137F
    if re.search(r'[\u1200-\u137F]', text):
        return ""
        
    # Arabic Unicode Range: \u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF, \uFB50-\uFDFF, \uFE70-\uFEFF
    if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
        return ""

    # At least one Latin alphabet character must exist (basic check for Afaan Oromoo/English)
    if not re.search(r'[a-zA-Z]', text):
        return ""

    return text

from typing import Dict

def process_data(data: list) -> dict:
    """
    Processes a list of post dictionaries, adhering to the original structure.
    """
    stats: Dict[str, int] = {
        "original_posts": len(data),
        "original_comments": sum(len(post.get("comments", [])) for post in data if isinstance(post, dict)),
        "original_tokens": 0,
        "removed_posts": 0,
        "removed_comments": 0,
        "final_posts": 0,
        "final_comments": 0,
        "final_tokens": 0
    }
    
    cleaned_data = []

    for post in data:
        if not isinstance(post, dict):
            continue
            
        original_post_text = post.get("post_text", "")
        # Add post original tokens
        if original_post_text and isinstance(original_post_text, str):
            stats["original_tokens"] += len(original_post_text.split())

        cleaned_post_text = clean_text_rule(original_post_text)
        
        # A post without text shouldn't necessarily be dropped according to earlier rules,
        # but the specific prompt says: "If a post ends up with zero valid comments, 
        # the post should still remain unless its own text fails validation."
        # This means if the post text fails validation, we drop the post entirely.
        if original_post_text and not cleaned_post_text:
             stats["removed_posts"] += 1
             stats["removed_comments"] += len(post.get("comments", []))
             continue # Drop the entire post
             
        # If it was originally empty but had comments, we keep it as empty? 
        # We will assume every post MUST have valid post_text to survive based on rule 1.
        if not cleaned_post_text:
             stats["removed_posts"] += 1
             stats["removed_comments"] += len(post.get("comments", []))
             continue
             
        new_post = post.copy()
        new_post["post_text"] = cleaned_post_text
        stats["final_tokens"] += len(cleaned_post_text.split())
        
        # Process Comments
        original_comments = post.get("comments", [])
        
        # If comments are stored as a JSON string (like from CSV), try to parse them
        if isinstance(original_comments, str):
            import json
            try:
                original_comments = json.loads(original_comments)
            except:
                original_comments = []

        cleaned_comments = []
        for comment in original_comments:
            if isinstance(comment, dict):
                original_cmt_text = comment.get("text", "")
                if original_cmt_text and isinstance(original_cmt_text, str):
                    stats["original_tokens"] += len(original_cmt_text.split())
                
                cleaned_cmt_text = clean_text_rule(original_cmt_text)
                
                if not cleaned_cmt_text:
                    stats["removed_comments"] += 1
                else:
                    new_cmt = comment.copy()
                    new_cmt["text"] = cleaned_cmt_text
                    cleaned_comments.append(new_cmt)
                    stats["final_tokens"] += len(cleaned_cmt_text.split())
            elif isinstance(comment, str):
                stats["original_tokens"] += len(comment.split())
                cleaned_cmt_text = clean_text_rule(comment)
                if not cleaned_cmt_text:
                    stats["removed_comments"] += 1
                else:
                    cleaned_comments.append(cleaned_cmt_text)
                    stats["final_tokens"] += len(cleaned_cmt_text.split())

        new_post["comments"] = cleaned_comments
        cleaned_data.append(new_post)
        
        stats["final_posts"] += 1
        stats["final_comments"] += len(cleaned_comments)

    return {
        "stats": stats,
        "cleaned_data": cleaned_data
    }
