from fastapi import APIRouter
def router(manager):
    r=APIRouter()
    @r.get('/health')
    async def health(): return {'status':'ok','providers':manager.status()}
    return r
