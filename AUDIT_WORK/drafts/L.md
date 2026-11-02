## Appendix L — Cost & Token Budget (v5.1, addition E)

### L.1 What costs money
- **LLM:** the Skill runs inside the Operator's Claude plan (Free/Pro/…): **marginal cost ₹0 per video** within plan limits (message quotas are the real limit — §14.1). For teams running it via the API, the API-equivalent cost is computed below with official prices. External research AI (Perplexity / Gemini / ChatGPT) and Gemini blueprints run in the Operator's own apps: ₹0 marginal on free tiers (quota-bound).
- **TTS:** `edge-tts` ₹0 (free unofficial endpoint, risk R13), `kokoro-onnx` ₹0 (local), ElevenLabs only if `RVS_PREMIUM_TTS=on` (per character).
- **Compute:** Operator phone / chat sandbox ₹0; a rented VM is `cloud_vm_per_hour` × Appendix K hours — no VM price is sourced, so it is excluded until the Operator sets it (DEC-16). Storage/egress: local files only, ₹0.

### L.2 Token & character estimates (ESTIMATE — method)
Tokens ≈ characters ÷ 4 for Latin/Hinglish context and ÷ 2 for Devanagari script text (rule-of-thumb; replace with the provider token counter when available). Per Long Master: SKILL.md + lazily loaded references (≈ 15k tokens per turn) × 5 turns + research dossier (≈ 8k) + 10 digest cards (≈ 2.5k) + growing history → **input 90k / 150k / 260k** (low / typical / high), **output 15k / 25k / 40k** (script ≈ 1,500 words in Devanagari ≈ 6k tokens + packs + code turns). Per derived clip: input 40k / 60k / 90k, output 4k / 6k / 10k. TTS characters: Long ≈ 1,500 words × 6 chars = 9,000 (7,000–13,500); derived clip ≈ 180 (2 fresh chunks).

### L.3 Prices (`cost/prices.json`, accessed 2 Nov 2026, re-check every 30 days)
```json
{
  "currency": "USD",
  "recheck_interval_days": 30,
  "accessed": "2026-11-02",
  "llm": {
    "claude-opus-5-5": {"input_per_mtok": 4.00, "output_per_mtok": 20.00, "cache_read_per_mtok": 0.20, "source": "https://platform.claude.com/docs/en/about-claude/pricing"},
    "claude-sonnet-5-5": {"input_per_mtok": 2.00, "output_per_mtok": 10.00, "cache_read_per_mtok": 0.10, "source": "https://platform.claude.com/docs/en/about-claude/pricing"}
  },
  "tts": {
    "edge-tts": {"per_1k_chars": 0.0, "source": "free Microsoft Edge read-aloud endpoint via rany2/edge-tts (unofficial; ToS caveat R13)"},
    "kokoro-onnx": {"per_1k_chars": 0.0, "source": "local (Apache-2.0 weights)"},
    "elevenlabs-multilingual-v2": {"per_1k_chars": 0.08, "source": "https://elevenlabs.io/pricing/api"}
  },
  "compute": {"operator_device_per_hour": 0.0, "cloud_vm_per_hour": null, "note": "cloud VM price not sourced → set by Operator; null = excluded"}
}
```

### L.4 Cost per Long Video and per Short Video (ESTIMATE; reproduced exactly by `python cost/cost_model.py --check`)
| Video type | Item | Low | Typical | High |
|---|---|---|---|---|
| Long (10-min master) | LLM API-equivalent (claude-opus-5-5) | $0.66 | $1.10 | $1.84 |
| Long (10-min master) | LLM API-equivalent (claude-sonnet-5-5) | $0.33 | $0.55 | $0.92 |
| Long (10-min master) | Premium TTS (ElevenLabs, only if toggled ON) | $0.56 | $0.72 | $1.08 |
| Long (10-min master) | Default TTS (edge-tts / kokoro-onnx) | $0.00 | $0.00 | $0.00 |
| Short (derived reel/short) | LLM API-equivalent (claude-opus-5-5) | $0.24 | $0.36 | $0.56 |
| Short (derived reel/short) | LLM API-equivalent (claude-sonnet-5-5) | $0.12 | $0.18 | $0.28 |
| Short (derived reel/short) | Premium TTS (ElevenLabs, only if toggled ON) | $0.01 | $0.01 | $0.02 |
| Short (derived reel/short) | Default TTS (edge-tts / kokoro-onnx) | $0.00 | $0.00 | $0.00 |

Formula: `LLM = in_tokens/1e6 × input_price + out_tokens/1e6 × output_price`; `TTS = chars/1000 × per_1k_chars`. Totals in INR only when the Operator sets `RVS_USD_INR` (no exchange rate is invented). Prompt caching (cache reads $0.20 / $0.10 per MTok) would lower repeated SKILL.md/reference input — not included (conservative).

### L.5 Free tiers, quotas & limits → codes
ElevenLabs Free = 10,000 characters/month (≈1 Long Master voice) — quota exhaustion → `RVS_WARN_044` → default engine. `edge-tts` throttling (403/429) → `RVS_WARN_041` → Kokoro. Claude plan message quotas → `RESUME PACK` (`RVS_WARN_123`).
