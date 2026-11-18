from fastapi import APIRouter,Header,HTTPException,Request
def router(application, secret):
    r=APIRouter()
    @r.post('/telegram/webhook')
    async def webhook(request:Request, x_telegram_bot_api_secret_token: str|None=Header(default=None)):
        if secret and x_telegram_bot_api_secret_token != secret: raise HTTPException(403,'invalid webhook secret')
        from telegram import Update
        await application.update_queue.put(Update.de_json(await request.json(), application.bot)); return {'ok':True}
    return r
