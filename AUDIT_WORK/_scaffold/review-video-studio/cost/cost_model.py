"""cost_model.py — recomputes Cost per Long Video / Short Video (App L) from cost/prices.json. --check: compare with expected_table.md."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ESTIMATE inputs (App L.2): tokens = chars/4 for Latin-Hinglish context, Devanagari script counted at chars/2 (method in App L)
SCEN = {
    "Long (10-min master)": {"in": (90_000, 150_000, 260_000), "out": (15_000, 25_000, 40_000), "tts_chars": (7_000, 9_000, 13_500)},
    "Short (derived reel/short)": {"in": (40_000, 60_000, 90_000), "out": (4_000, 6_000, 10_000), "tts_chars": (150, 180, 300)},
}


def table(prices):
    rows = ["| Video type | Item | Low | Typical | High |", "|---|---|---|---|---|"]
    for name, s in SCEN.items():
        for model in ("claude-opus-5-5", "claude-sonnet-5-5"):
            p = prices["llm"][model]
            v = [s["in"][i] / 1e6 * p["input_per_mtok"] + s["out"][i] / 1e6 * p["output_per_mtok"] for i in range(3)]
            rows.append(f"| {name} | LLM API-equivalent ({model}) | ${v[0]:.2f} | ${v[1]:.2f} | ${v[2]:.2f} |")
        e = prices["tts"]["elevenlabs-multilingual-v2"]["per_1k_chars"]
        t = [s["tts_chars"][i] / 1000 * e for i in range(3)]
        rows.append(f"| {name} | Premium TTS (ElevenLabs, only if toggled ON) | ${t[0]:.2f} | ${t[1]:.2f} | ${t[2]:.2f} |")
        rows.append(f"| {name} | Default TTS (edge-tts / kokoro-onnx) | $0.00 | $0.00 | $0.00 |")
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    prices = json.load(open(os.path.join(HERE, "prices.json"), encoding="utf-8"))
    t = table(prices)
    exp = os.path.join(HERE, "expected_table.md")
    if "--check" in sys.argv:
        ok = os.path.exists(exp) and open(exp, encoding="utf-8").read() == t
        print("cost table matches" if ok else "cost table MISMATCH (prices changed? regenerate + update App L)")
        sys.exit(0 if ok else 1)
    if "--write" in sys.argv:
        open(exp, "w", encoding="utf-8").write(t)
    print(t)
    fx = os.environ.get("RVS_USD_INR")  # Operator-supplied rate only (DEC-16); never invented
    if fx:
        print(f"INR view: multiply every USD cell by {float(fx):.2f} (rate supplied by Operator via RVS_USD_INR)")
