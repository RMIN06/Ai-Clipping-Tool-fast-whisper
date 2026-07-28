# CELL 3: FIXED PIPELINE & SUBTITLE GENERATOR
from faster_whisper import WhisperModel
import ollama
import json
import os
import subprocess
import time

# 1. Verify Video Path
video_path = "/content/drive/MyDrive/podcast"
if not os.path.exists(video_path):
    if os.path.exists(video_path + ".mp4"):
        video_path = video_path + ".mp4"
    else:
        raise FileNotFoundError(f"Could not find video at {video_path}")

print(f"✅ Found video at: {video_path}")

# 2. Transcribe with Faster-Whisper
print("\nLoading transcription AI (Faster-Whisper)...")
model = WhisperModel("small", device="cuda", compute_type="float16")

print("Extracting audio and word timestamps...")
segments, info = model.transcribe(video_path, word_timestamps=True)

word_data = []
transcript_text = ""

for segment in segments:
    for word in segment.words:
        w_text = word.word.strip()
        transcript_text += f"[{word.start:.1f}s] {w_text} "
        word_data.append({"word": w_text, "start": word.start, "end": word.end})

print("\nTranscription complete. Analyzing for 40-55 second highlights with Ollama...")

# 3. Aggressive Prompt for 40-55s Clips
prompt = f"""
You are an expert short-form video editor. Analyze this podcast transcript.
Find 5 to 7 engaging highlights.
CRITICAL RULE: Each highlight MUST have a duration between 40 and 55 seconds (i.e., (end - start) must be between 40 and 55).
Return ONLY a strict JSON array of objects with keys: "start", "end", and "reason". Do not wrap it in any other dictionary keys.

Example format:
[
  {{"start": 12.0, "end": 55.0, "reason": "Strong hook about business growth"}},
  {{"start": 120.0, "end": 165.0, "reason": "Controversial statement about tech"}}
]

Transcript (truncated):
{transcript_text[:15000]}
"""

response = ollama.generate(
    model="llama3.2",
    prompt=prompt,
    format="json"
)

raw_json = response["response"]

# --- 4. PARSE & ADJUST CLIPS TO 40-55 SECONDS ---
try:
    if "```json" in raw_json:
        raw_json = raw_json.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_json:
        raw_json = raw_json.split("```")[1].split("```")[0].strip()

    parsed = json.loads(raw_json)

    if isinstance(parsed, dict):
        clips = parsed.get("clips", parsed.get("transcript", [parsed]))
    elif isinstance(parsed, list):
        clips = parsed
    else:
        clips = []

    valid_clips = []
    for clip in clips:
        if "start" in clip and "end" in clip:
            s = float(clip["start"])
            e = float(clip["end"])
            duration = e - s

            # AUTOMATIC CORRECTION: If the clip is too short, extend the end time to hit ~45 seconds
            if duration < 40:
                e = s + 45.0
            # If the clip is too long, trim it down to 50 seconds
            elif duration > 55:
                e = s + 50.0

            clip["start"] = s
            clip["end"] = e
            clip["words"] = [w for w in word_data if s <= w["start"] <= e]
            valid_clips.append(clip)

    # If the AI failed to return structured clips, auto-slice the video into 45-second chunks
    if len(valid_clips) == 0:
        print("⚠️ AI didn't return valid clips. Generating automatic 45-second intervals from the transcript...")
        total_duration = word_data[-1]["end"] if word_data else 300
        for i in range(0, int(total_duration), 50):
            s = float(i)
            e = float(min(i + 45, total_duration))
            if (e - s) >= 30:
                chunk_words = [w for w in word_data if s <= w["start"] <= e]
                valid_clips.append({"start": s, "end": e, "reason": "Auto-sliced segment", "words": chunk_words})

    clips = valid_clips[:7] # Cap at 7 clips max
    print(f"\n🎬 Success! Locked in {len(clips)} viral clips (guaranteed 40-55s each).")

    for i, c in enumerate(clips, 1):
        print(f"\nClip {i}: Start: {c['start']:.1f}s | End: {c['end']:.1f}s (Duration: {c['end'] - c['start']:.1f}s)")
        print(f"Reason: {c.get('reason', 'N/A')}")

except Exception as e:
    print(f"❌ Error parsing response: {e}")
    print("Raw Response was:", raw_json)
    clips = []