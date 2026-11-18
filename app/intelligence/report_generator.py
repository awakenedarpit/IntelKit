import json
REPORT_PROMPT='You are IntelKit, a concise content intelligence analyst. Extract signal, not noise.\nReturn ONLY valid JSON with an array called sections. Each section has title and bullets. Valid titles: Main Takeaway, Key Information, Practical Knowledge, Important Context, Claims Worth Verifying, Actionable Takeaways, Short Summary. Omit irrelevant sections. Do not invent facts, repeat points, narrate scenes, or provide captions. Mark uncertain creator claims as unverified.\nContent to analyze:\n'
def format_report(raw: str, provider='unknown') -> str:
    try:
        data=json.loads(raw); sections=data.get('sections',[])
        chunks=[]
        for s in sections:
            title=str(s.get('title','')).strip(); bullets=s.get('bullets',[])
            if title and bullets: chunks.append('**'+title+'**\n'+'\n'.join('• '+str(x).strip() for x in bullets if str(x).strip()))
        if chunks: return '\n\n'.join(chunks)+f"\n\n_Analyzed with {provider}._"
    except (json.JSONDecodeError, TypeError): pass
    return raw.strip() or 'The content did not contain enough useful information to summarize.'
