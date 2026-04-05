from typing import List, Dict

try:
    import whisper
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False

IMPACT_WORDS_EN = {
    "NEVER", "NOBODY", "IMPOSSIBLE", "CLASSIFIED", "SECRET",
    "DEAD", "VANISHED", "DISAPPEARED", "HIDDEN", "TRUTH",
    "UNKNOWN", "UNEXPLAINED", "ONLY", "EVIDENCE",
}


def _t(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _build_ass(chunks: List[Dict[str, object]]) -> str:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Normal,Arial Black,82,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,4,2,2,80,80,300,1
Style: Impact,Arial Black,90,&H0000FFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,5,3,2,80,80,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for c in chunks:
        style = "Impact" if c["impact"] else "Normal"
        lines.append(f"Dialogue: 0,{_t(c['start'])},{_t(c['end'])},{style},,0,0,0,,{{\\fad(80,80)}}{c['text']}")
    return "\n".join(lines)


def generate_documentary_subs_en(audio_path: str, output_ass: str) -> str:
    chunks = []

    if WHISPER_AVAILABLE:
        try:
            model = whisper.load_model("small")
            result = model.transcribe(audio_path, language="en", word_timestamps=True)
            words = []
            for seg in result.get("segments", []):
                words.extend(seg.get("words", []))

            i = 0
            while i < len(words):
                w0 = words[i]
                token = str(w0.get("word", "")).strip().upper().rstrip(".,!?")
                if token in IMPACT_WORDS_EN:
                    group = [w0]
                    i += 1
                else:
                    group = words[i:i + 2]
                    i += 2

                text = " ".join(str(w.get("word", "")).strip().upper() for w in group).strip()
                if not text:
                    continue
                chunks.append({
                    "text": text,
                    "start": float(group[0].get("start", 0.0)),
                    "end": float(group[-1].get("end", group[0].get("start", 0.4))),
                    "impact": any(str(w.get("word", "")).strip().upper().rstrip(".,!?") in IMPACT_WORDS_EN for w in group),
                })
        except Exception:
            chunks = []

    if not chunks:
        chunks = [
            {"text": "UNRESOLVED CASE", "start": 0.0, "end": 1.2, "impact": True},
            {"text": "EVIDENCE REMAINS", "start": 1.2, "end": 2.4, "impact": False},
            {"text": "NO FINAL ANSWER", "start": 2.4, "end": 3.6, "impact": True},
        ]

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(_build_ass(chunks))

    return output_ass
