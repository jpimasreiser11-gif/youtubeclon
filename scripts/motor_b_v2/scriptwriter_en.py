import json
import random
from typing import Dict, Any

try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

VIRAL_TOPICS = {
    "mystery": [
        "The Dyatlov Pass Incident: 9 hikers died and the cause was classified for 60 years",
        "The Tamam Shud Case: the unidentified man with a cipher nobody has cracked",
        "DB Cooper: the only unsolved hijacking in US aviation history",
        "The Voynich Manuscript: 600 years and no language matches it",
        "The Wow! Signal: a radio transmission from space received once and never again",
    ],
    "paranormal": [
        "The Enfield Poltergeist: the most documented haunting ever recorded on audio",
        "The Skinwalker Ranch: the US government secretly bought this property",
        "The Rendlesham Forest incident: UFO witnessed by NATO base personnel",
        "The Hessdalen Lights: Norway's unexplained orbs studied for decades",
    ],
    "historical_enigma": [
        "The Antikythera Mechanism: an ancient computer far ahead of its time",
        "The Baghdad Battery: a 2,000-year-old device that may generate electricity",
        "The Piri Reis Map and the Antarctica controversy",
        "The Roman dodecahedra nobody can explain",
    ],
}

HOOKS_EN = [
    "This happened. And nobody has explained it.",
    "The official story sounds clean. The evidence does not.",
    "There are details in this case that still make experts uncomfortable.",
    "What you are about to hear is all documented. And still unresolved.",
]

SCRIPT_PROMPT_EN = """
Write a 60-75 second English mystery narration script.
Topic: {topic}
Opening hook: {hook}
Max words: {word_count}

Strict structure:
1) Hook in first 2 lines.
2) Context with concrete facts.
3) Escalation with 3-4 evidence beats.
4) Buried detail almost nobody mentions.
5) Open ending with one direct question.

Rules:
- No filler words.
- Sentences under 18 words.
- Verifiable framing, no invented stats.
- Plain text only.
"""


def _fallback_script(topic: str, hook: str) -> str:
    return (
        f"{hook} In this case, the timeline is clear, but the explanation is not. "
        f"The event started with a routine situation and ended with evidence that contradicts the official report. "
        f"Witnesses agreed on key details, yet the records were fragmented and delayed. "
        f"But here is what almost nobody mentions: one document was archived under a different label years later. "
        f"If the known explanation was complete, why is this case still debated today?"
    )


def generate_script_en(topic: str = None, category: str = "mystery", duration_sec: int = 65) -> Dict[str, Any]:
    if not topic:
        topic = random.choice(VIRAL_TOPICS.get(category, VIRAL_TOPICS["mystery"]))
    hook = random.choice(HOOKS_EN)
    word_count = int(duration_sec * (160 / 60))

    if OLLAMA_AVAILABLE:
        try:
            prompt = SCRIPT_PROMPT_EN.format(topic=topic, hook=hook, word_count=word_count)
            response = ollama.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.72, "num_predict": 900, "top_p": 0.92},
            )
            script = (response.get("message") or {}).get("content", "").strip()
            if not script:
                script = _fallback_script(topic, hook)
        except Exception:
            script = _fallback_script(topic, hook)
    else:
        script = _fallback_script(topic, hook)

    title_a = f"{topic.split(':')[0]}: What Was Never Explained"[:90]
    title_b = f"5 Facts About {topic.split(':')[0]} They Buried"[:90]
    title_c = f"{topic.split(':')[0]}: The Unsolved Detail"[:90]

    return {
        "topic": topic,
        "category": category,
        "script": script,
        "hook": hook,
        "word_count": len(script.split()),
        "estimated_duration": len(script.split()) / (160 / 60),
        "visual_prompts": [
            "abandoned corridor, practical flashlight beam, cinematic shadows, documentary style",
            "old archive papers on table, moody top light, film grain",
            "foggy forest path at night, cold color palette, suspense",
            "silhouette near doorway, atmospheric haze, realistic lighting",
            "dark sky with distant lights, dramatic cloud texture",
        ],
        "title_a": title_a,
        "title_b": title_b,
        "title_c": title_c,
        "tags": [
            "mystery", "unsolved", "paranormal", "history", "documentary",
            "true mystery", "conspiracy", "cold case", "evidence", "investigation",
        ],
        "description_hook": f"{topic.split(':')[0]} remains one of the most debated unresolved cases.",
    }


if __name__ == "__main__":
    data = generate_script_en()
    print(json.dumps(data, indent=2, ensure_ascii=False))
