import os
import re
import subprocess
from typing import List


def _prepare_script_for_tts(script: str) -> str:
    text = script or ""
    reveal_phrases = [
        "but here's", "what almost no", "what the official",
        "the detail that", "there's only one", "what nobody mentions",
    ]
    for phrase in reveal_phrases:
        text = text.replace(phrase, f"\n{phrase}")
    text = re.sub(r"(\d+ years|\d+ people|\d+ days|\d+ hours)", r"\1.", text)
    return text


def _concat_wavs(files: List[str], output_path: str):
    list_file = os.path.join(os.path.dirname(output_path), "concat_voice.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-ar", "44100", "-ac", "1", output_path,
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def generate_narration_en(script: str, output_dir: str, device: str = "cpu") -> str:
    os.makedirs(output_dir, exist_ok=True)
    prepared = _prepare_script_for_tts(script)
    parts = [p.strip() for p in prepared.split("\n") if p.strip()]

    segs = []
    for i, part in enumerate(parts):
        seg = os.path.join(output_dir, f"seg_{i:02d}.wav")
        ok = False

        # Preferred: Chatterbox
        try:
            from chatterbox.tts import ChatterboxTTS
            import torchaudio as ta

            model = ChatterboxTTS.from_pretrained(device=device)
            wav = model.generate(part, exaggeration=0.6 if i > 0 else 0.75, cfg_weight=0.4)
            ta.save(seg, wav, model.sr)
            ok = True
        except Exception:
            ok = False

        # Fallback: Edge-TTS
        if not ok:
            try:
                import asyncio
                import edge_tts

                async def _gen():
                    tts = edge_tts.Communicate(part, voice="en-US-GuyNeural", rate="-8%", pitch="-10Hz")
                    await tts.save(seg)

                asyncio.run(_gen())
                ok = True
            except Exception:
                ok = False

        # Last fallback: short silence
        if not ok:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "1.0", seg,
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        segs.append(seg)

    final_path = os.path.join(output_dir, "narration_final.wav")
    _concat_wavs(segs, final_path)
    return final_path
