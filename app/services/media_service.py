import asyncio, subprocess
from pathlib import Path
async def extract_frames(video, out_dir, count=6):
    out=Path(out_dir)/'frame-%02d.jpg'
    cmd=['ffmpeg','-y','-i',str(video),'-vf',f"fps=1/{max(1,30//count)}",'-frames:v',str(count),str(out)]
    proc=await asyncio.create_subprocess_exec(*cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE); await proc.communicate()
    return sorted(Path(out_dir).glob('frame-*.jpg')) if proc.returncode==0 else []
async def extract_audio(video, output):
    cmd=['ffmpeg','-y','-i',str(video),'-vn','-acodec','mp3',str(output)]
    proc=await asyncio.create_subprocess_exec(*cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE); await proc.communicate(); return proc.returncode==0
