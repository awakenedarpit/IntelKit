from pathlib import Path
from app.services.media_service import extract_frames, extract_audio
async def process(path, extractor, workspace):
    frames=await extract_frames(path,workspace); audio=await extract_audio(path,Path(workspace)/'audio.mp3')
    imgs=[p.read_bytes() for p in frames]
    note=f"Uploaded video. Extracted {len(frames)} representative frames; audio extraction {'succeeded' if audio else 'failed'}. Speech transcription is only included when configured."
    return await extractor.analyze(note,imgs)
