def generate_simple_srt(text, srt_path):
    words = text.split()
    if not words:
        words = ["SIN", "CONTENIDO"]

    chunk = 3
    lines = []
    idx = 1
    current = 0.0
    per_chunk = 1.2

    for i in range(0, len(words), chunk):
        block = " ".join(words[i:i+chunk]).upper()
        start = current
        end = current + per_chunk
        lines.append(f"{idx}\n{_ts(start)} --> {_ts(end)}\n{block}\n")
        idx += 1
        current = end

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return srt_path


def _ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
