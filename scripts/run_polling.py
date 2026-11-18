from app.config import get_settings
from app.providers.manager import AIProviderManager
from app.bot.client import build_application
from app.intelligence.extractor import IntelligenceExtractor
s=get_settings(); m=AIProviderManager(s); build_application(s,m,IntelligenceExtractor(m)).run_polling()
