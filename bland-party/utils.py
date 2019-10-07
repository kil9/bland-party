import hashlib

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def get_score(word: str):
    digest = hashlib.sha256(word.encode()).hexdigest()
    o = 0
    for c in digest:
        o += ord(c)
    out = o % 1000
    if out == 0:
        out = 1000

    return out/10.0

def moved_step_str(old: int, new: int):
    moved = abs(new - old)
    if old > new:
        arrow = '↑'
    elif old < new:
        arrow = '↓'
    else:
        arrow = '→'

    return f'({arrow}{moved})'
