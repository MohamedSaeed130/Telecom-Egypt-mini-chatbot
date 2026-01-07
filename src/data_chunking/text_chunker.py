import re
from typing import List

def recursive_chunk(text, max_size, level=0):
    text = text.strip()
    if not text:
        return []

    # If the text is already within the max size, return it as a single chunk
    if len(text) <= max_size:
        return [text]

    # Define separators for different levels of chunking
    # 1. Paragraphs
    # 2. Sentences (Arabic/English) 
    # 3. Newlines
    # 4. Words (Spaces)
    separators = [
    r'\n{2,}',                      # Paragraphs
    r'(?<=[.!؟!?])',             # Sentences (AR + EN)
    r'(?<=[،,؛;:])',              # Clauses
    r'\n\s*[-•*]',               # Bullet points
    r'\s+'                          # Whitespace fallback
    ]

    # If we ran out of separators, force split by size
    if level >= len(separators):
        return [text[i:i + max_size] for i in range(0, len(text), max_size)]

    separator = separators[level]
    
    # Split the text
    chunks = re.split(separator, text)
    chunks = [c.strip() for c in chunks if c.strip()]
    
    # If splitting didn't reduce the chunk (separator not found), try next level immediately
    if len(chunks) == 1 and len(chunks[0]) > max_size:
        return recursive_chunk(text, max_size, level + 1)
        
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_size:
            final_chunks.extend(recursive_chunk(chunk, max_size, level + 1))
        else:
            final_chunks.append(chunk)

    return final_chunks
