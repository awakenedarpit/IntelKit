import logging
from fastapi import FastAPI
from .config import get_settings
from .utils.logging_config import configure_logging
from .providers.manager import AIProviderManager
from .intelligence.extractor import IntelligenceExtractor
from .api.health import router as health_router
from .api.webhook import router as webhook_router
settings=get_settings(); configure_logging(settings.log_level); log=logging.getLogger(__name__)
manager=AIProviderManager(settings); extractor=IntelligenceExtractor(manager)
app=FastAPI(title='IntelKit',version='1.0.0')
app.include_router(health_router(manager))
if settings.app_env=='production':
    try:
        from .bot.client import build_application
        telegram_app=build_application(settings,manager,extractor); app.include_router(webhook_router(telegram_app,settings.telegram_webhook_secret))
    except RuntimeError as e: log.warning('Telegram webhook disabled: %s',e)
@app.get('/')
async def root(): return {'name':'IntelKit','tagline':'AI-Powered Content Intelligence','environment':settings.app_env}
