from .report_generator import REPORT_PROMPT, format_report
class IntelligenceExtractor:
    def __init__(self, manager): self.manager=manager
    async def analyze(self, text, images=None):
        result=await self.manager.analyze(REPORT_PROMPT+text, images=images)
        return format_report(result.text, result.provider)
