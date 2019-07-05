import hashlib

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def get_score(word: str):
    digest = hashlib.sha256(word.encode()).hexdigest()
    o = 0
    for c in digest:
        o += ord(c)
    out = o % 100
    if out == 0:
        out = 100
    return out
