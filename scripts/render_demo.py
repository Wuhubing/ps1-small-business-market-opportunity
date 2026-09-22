"""Build a five-minute narrated walkthrough from real captured website states.

Requirements: macOS say (Samantha), ffmpeg/ffprobe, and Pillow.
Run capture_demo.cjs first. Intermediate media stays in .sites-runtime/video.
"""
from pathlib import Path
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.sites-runtime/video'
OUT = ROOT / 'docs/media'
OUT.mkdir(parents=True, exist_ok=True)
SCENES = json.loads((ROOT / 'presentation/video-scenes.json').read_text())
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
titlefont = ImageFont.truetype(BOLD, 27)
captionfont = ImageFont.truetype(FONT, 27)
smallfont = ImageFont.truetype(FONT, 18)

def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)]))

def stamp(seconds):
    milliseconds = round(seconds * 1000)
    return f'{milliseconds//3600000:02}:{milliseconds//60000%60:02}:{milliseconds//1000%60:02}.{milliseconds%1000:03}'

def frame(scene, title, caption, filename):
    image = Image.new('RGB',(1440,1080),'#102a36')
    screenshot = Image.open(WORK / f'{scene}.png').convert('RGB')
    image.paste(screenshot,(0,72))
    d=ImageDraw.Draw(image)
    d.text((32,22),title,font=titlefont,fill='#c8e35b')
    d.text((1100,26),'5-MINUTE SITE WALKTHROUGH',font=smallfont,fill='white')
    words=caption.split(); lines=[]; line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if d.textlength(candidate,font=captionfont)>1360:
            lines.append(line); line=word
        else: line=candidate
    if line: lines.append(line)
    for i,line in enumerate(lines):
        d.text((40,935+i*36),line,font=captionfont,fill='white')
    d.text((40,1044),'Actual website views • English synthetic narration • September 2025 decision snapshot',font=smallfont,fill='#b8cbce')
    d.rectangle((0,1074,int(1440*scene/12),1080),fill='#c8e35b')
    image.save(filename)

video_lines=[]; audio_lines=[]; captions=['WEBVTT','']; transcript=['# Five-minute website walkthrough','','English synthetic narration (macOS Samantha). Actual website states captured from the project.','']
elapsed=0
for number,scene in enumerate(SCENES,1):
    clips=[]
    for j,sentence in enumerate(scene['sentences']):
        audio=WORK/f'{number}-{j}.aiff'
        run(['say','-v','Samantha','-r','155','-o',str(audio),sentence])
        clips.append((sentence,audio,duration(audio)))
    speech_total=sum(c[2] for c in clips)
    # Leave at least a short pause after every chapter; cap speech at 24 seconds.
    speed=max(1.0,speech_total/24.0)
    transcript += [f'## {stamp((number-1)*25)[:8]} — {scene["title"]}', '', ' '.join(scene['sentences']), '']
    for j,(sentence,audio,_) in enumerate(clips):
        wav=WORK/f'{number}-{j}.wav'
        run(['ffmpeg','-y','-i',str(audio),'-af',f'atempo={speed}','-ar','24000','-ac','1',str(wav)])
        seconds=duration(wav)
        png=WORK/f'frame-{number}-{j}.png'
        frame(number,scene['title'],sentence,png)
        video_lines += [f"file '{png}'",f'duration {seconds:.6f}']
        audio_lines += [f"file '{wav}'"]
        captions += [f'{stamp(elapsed)} --> {stamp(elapsed+seconds)}',sentence,'']
        elapsed+=seconds
    remaining=number*25-elapsed
    silence=WORK/f'pause-{number}.wav'
    run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t',str(remaining),str(silence)])
    audio_lines += [f"file '{silence}'"]
    video_lines[-1]=f'duration {seconds+remaining:.6f}'
    elapsed=number*25
    print(f'Prepared chapter {number}/12 ({speech_total:.1f}s original narration)',flush=True)

video_lines.append(video_lines[-2])
(WORK/'frames.txt').write_text('\n'.join(video_lines)+'\n')
(WORK/'audio.txt').write_text('\n'.join(audio_lines)+'\n')
(OUT/'walkthrough-en.vtt').write_text('\n'.join(captions))
(OUT/'walkthrough-transcript.md').write_text('\n'.join(transcript))
run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(WORK/'frames.txt'),'-f','concat','-safe','0','-i',str(WORK/'audio.txt'),'-map','0:v:0','-map','1:a:0','-vf','fps=10','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-t','300','-movflags','+faststart',str(OUT/'cambridge-walkthrough-5min.mp4')])
Image.open(WORK/'frame-1-0.png').save(OUT/'walkthrough-poster.jpg',quality=88)
print(json.dumps({'duration':duration(OUT/'cambridge-walkthrough-5min.mp4'),'bytes':(OUT/'cambridge-walkthrough-5min.mp4').stat().st_size,'output':str(OUT/'cambridge-walkthrough-5min.mp4')}))
