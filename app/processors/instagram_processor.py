import re, httpx
from pathlib import Path
IG_RE=re.compile(r"https?://(?:www\.)?instagram\.com/(reel|p|tv)/[^/?#]+",re.I)
def classify(url):
    m=IG_RE.fullmatch(url.strip().rstrip('/'))
    return m.group(1).lower() if m else None
async def retrieve(url, workspace):
    kind=classify(url)
    if not kind: raise ValueError('Unsupported Instagram URL. Send a public /reel/, /p/, or /tv/ link.')
    async with httpx.AsyncClient(follow_redirects=True,timeout=20,headers={'User-Agent':'IntelKit/1.0'}) as c: r=await c.get(url)
    if r.status_code!=200: raise RuntimeError('Instagram content could not be retrieved publicly. Please upload the media directly.')
    # Public metadata is best-effort and never bypasses access controls.
    m=re.search(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)",r.text,re.I)
    if not m: raise RuntimeError('Instagram media was not publicly retrievable. Please upload it directly.')
    data=await c.get(m.group(1)); p=Path(workspace)/'instagram.jpg'; p.write_bytes(data.content); return kind,p
