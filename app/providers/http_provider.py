import base64, httpx
from .base import BaseProvider, ProviderError, ProviderResult
class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, name, api_key, model, base_url, supports_vision=True): self.name=name; self.api_key=api_key; self.model=model; self.base_url=base_url; self.supports_vision=supports_vision
    async def analyze(self, prompt, images=None):
        if not self.api_key: raise ProviderError(f"{self.name} credentials are not configured")
        content=[{"type":"text","text":prompt}]
        for img in images or []: content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(img).decode()}})
        payload={"model":self.model,"messages":[{"role":"user","content":content}],"temperature":0.1}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r=await client.post(self.base_url+"/chat/completions", headers={"Authorization":"Bearer "+self.api_key}, json=payload)
            if r.status_code in (429,500,502,503): raise ProviderError(f"{self.name} temporary error {r.status_code}", True)
            if r.status_code>=400: raise ProviderError(f"{self.name} request failed ({r.status_code})")
            data=r.json(); return ProviderResult(data['choices'][0]['message']['content'], self.name, self.model)
        except httpx.TimeoutException as e: raise ProviderError(f"{self.name} timed out", True) from e
        except httpx.RequestError as e: raise ProviderError(f"{self.name} network error", True) from e
