import asyncio
class AlbumCollector:
    def __init__(self): self.pending={}
    async def add(self, group_id, path, process):
        entry=self.pending.setdefault(group_id,[]); entry.append(path); await asyncio.sleep(1.2)
        if self.pending.get(group_id)==entry:
            self.pending.pop(group_id,None); return await process(sorted(entry))
