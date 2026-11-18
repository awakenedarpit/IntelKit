import logging
from .base import ProviderError
from .http_provider import OpenAICompatibleProvider
log=logging.getLogger(__name__)
class AIProviderManager:
    def __init__(self, settings):
        self.settings=settings; self.providers={
          'groq':OpenAICompatibleProvider('groq',settings.groq_api_key,settings.groq_model,'https://api.groq.com/openai/v1'),
          'gemini':OpenAICompatibleProvider('gemini',settings.gemini_api_key,settings.gemini_model,'https://generativelanguage.googleapis.com/v1beta/openai'),
          'openrouter':OpenAICompatibleProvider('openrouter',settings.openrouter_api_key,settings.openrouter_model,'https://openrouter.ai/api/v1')}
        self.usage={k:0 for k in self.providers}
    def ordered_names(self): return list(dict.fromkeys([self.settings.primary_provider]+self.settings.fallback_list))
    def status(self): return {n: bool(self.providers[n].api_key) for n in self.providers}
    async def analyze(self,prompt,images=None):
        errors=[]
        for name in self.ordered_names():
            p=self.providers.get(name)
            if not p: continue
            try:
                result=await p.analyze(prompt,images); self.usage[name]+=1; return result
            except ProviderError as e:
                errors.append(f"{name}: {e}"); log.warning("provider failed: %s", e)
                if not e.retryable and p.api_key: continue
        raise RuntimeError("All configured AI providers failed: " + "; ".join(errors))
