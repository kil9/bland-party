import hashlib

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def get_score(word: str):
    digest = hashlib.sha256(word.encode()).hexdigest()
    o = 0
    for c in digest:
        o += ord(c)
    return o % 100
