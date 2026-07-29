# CELL 4: RENDER CLIPS WITH VIRAL SUBTITLES
import os
import subprocess

OUTPUT_DIR = "/content/drive/MyDrive/Viral_Clips"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_ass_file(words, ass_path):
    """Creates a TikTok-style dynamic word-by-word subtitle file (.ass)"""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,80,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,0,2,10,10,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt_t(secs):
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = secs % 60
        return f"{h:01d}:{m:02d}:{s:05.2f}"

    lines = [header]
    chunk_size = 4 # Group 4 words at a time for fast readability

    for i in range(0, len(words), chunk_size):
        chunk = words[i:i+chunk_size]
        if not chunk: continue

        start_t = fmt_t(max(0.0, chunk[0]['start'] - words[0]['start']))
        end_t = fmt_t(max(0.0, chunk[-1]['end'] - words[0]['start']))

        text = " ".join([w['word'].upper() for w in chunk])
        lines.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{text}\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

print(f"🚀 Rendering {len(clips)} vertical clips with subtitles...")

for idx, clip in enumerate(clips, 1):
    start_sec = clip["start"]
    end_sec = clip["end"]
    clip_words = clip.get("words", [])

    ass_file = f"/content/clip_{idx}.ass"
    out_mp4 = os.path.join(OUTPUT_DIR, f"viral_clip_{idx}.mp4")

    # Shift word times relative to the start of this specific clip
    shifted_words = [{'word': w['word'], 'start': w['start'] - start_sec, 'end': w['end'] - start_sec} for w in clip_words]
    create_ass_file(shifted_words, ass_file)

    # FFmpeg filter: Crop 16:9 to 9:16 vertical + burn in subtitles
    filter_complex = f"crop=ih*(9/16):ih:(iw-ow)/2:0,subtitles='{ass_file}'"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-to", str(end_sec),
        "-i", video_path,
        "-vf", filter_complex,
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        out_mp4
    ]

    print(f"Processing Clip {idx} ({end_sec - start_sec:.1f}s)...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"✅ Saved: {out_mp4}")

print("\n🎉 Done! Go check your Google Drive -> 'Viral_Clips' folder.")