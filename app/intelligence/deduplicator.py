def deduplicate(items):
    seen=set(); out=[]
    for item in items:
        key=' '.join(str(item).lower().split())
        if key and key not in seen: seen.add(key); out.append(item)
    return out
