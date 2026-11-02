## Appendix O — Studio Voice Module (Module M1: Engine Adapter, Mastering Chain, Premium Path, Voice Tests)

### O.1 Baseline (v5.0) and v5.1 engine design
- **v5.0 baseline:** `edge-tts` (`hi-IN-MadhurNeural` `+6%`) per chunk → double-reverse `silenceremove` → 48 kHz stereo → mix → two-pass `loudnorm` (−14 LUFS). Weaknesses (evidence: §7.2/G.2 v5.0): no EQ, no de-essing, no dynamics control; per-chunk `espeak-ng` mixing and a silent sine-beep fallback (D-041/D-126); archived local engine listed; cache not engine-keyed (D-125).
- **v5.1 adapter contract (`voice_engines.py`, G.10):** `synth(text, lang, voice_id, rate, pitch, out_path, sem) → {wav, engine, engine_version}`; output normalised to 48 kHz s16 stereo by `trim_chunk_silence_48k_stereo`; `normalize_tts_say` runs **before every engine**; mastering runs **after** (O.2).
- **Engine order (DEC-03):** `[elevenlabs — only if RVS_PREMIUM_TTS=on AND key]` → `edge-tts` (default, online) → **`kokoro-onnx` = Primary HQ LOCAL engine** → `espeak-ng` (floor). The whole run stays on one engine; a failure re-synthesises all chunks on the next engine (`RVS_WARN_041`); nothing works → `RVS_ERR_040`. `words.json.engine` records provenance.

### O.2 Mastering chain `RVS-VOICE-MASTER-v1` (MEASURED 2 Nov 2026, FFmpeg 6.1.1)
Applied to the voice stem inside the mix filtergraph (G.3 `mix_and_normalize_audio_two_pass`), before the final two-pass `loudnorm` (`I=-14:TP=-1.5:LRA=11`, PRD target — LOUDNESS_RULE):
```text
highpass=f=70:poles=2,                          # remove rumble/DC below the voice fundamental
lowshelf=f=160:g=3,                             # +3 dB warmth (podcast-mic body)
equalizer=f=3000:t=q:w=1.0:g=1.0,                # +1 dB presence / intelligibility
highshelf=f=6000:g=-4,                          # −4 dB above 6 kHz — tames TTS sibilance and harshness
deesser=i=0.6:m=0.5:f=0.5:s=o,                  # dynamic de-esser safety net
acompressor=threshold=-20dB:ratio=2:attack=10:release=150:makeup=1:knee=4,   # gentle 2:1 levelling across chunks
alimiter=limit=0.89:attack=5:release=50:level=disabled                      # ≈ −1.0 dBFS sample ceiling before loudnorm
```
- **Fallback** `RVS_VOICE_MASTER=safe`: `highpass=f=70,lowshelf=f=160:g=3,highshelf=f=6000:g=-4,acompressor=threshold=-20dB:ratio=2:attack=10:release=150` (filters present in FFmpeg ≥4.4 incl. Debian 12's 5.1); **bypass** `RVS_VOICE_MASTER=off`. Filter failure → automatic fallback → bypass with `RVS_WARN_053` — the build never aborts.
- **Verification protocol & results** (3 Hindi clips synthesised locally with Kokoro: female `hf_alpha`, male `hm_omega`, sibilant+numbers `hm_psi`; generic audit sentences, no PRD text left the machine). Every filter/option confirmed with `ffmpeg -h filter=NAME` on 6.1.1. Candidates measured with `ebur128` (I, LRA, true peak) + numpy FFT band levels after loudness matching:

| Chain | I (LUFS) f / m / s | True peak (dBTP) | Clipped samples | Sibilance 5–9 kHz vs baseline (dB) | Warmth <250 Hz vs baseline (dB) | Decision |
|---|---|---|---|---|---|---|
| Baseline (loudnorm only) | −13.8 / −14.0 / −14.0 | −1.6 / −1.5 / −1.5 | 0 | 0 | 0 | reference |
| A — prompt hypothesis `bass=g=4:f=110,treble=g=2,compand=…` | −13.8 / −13.8 / −13.9 | −4.3 / −2.8 / −1.9 | 0 | **+3.03 / +2.56 / +2.56** | +0.89 / +1.10 / +0.98 | rejected (sibilance up) |
| B — EQ + presence 3.5 kHz + deesser + acompressor + alimiter | −13.9 / −14.0 / −14.0 | −3.6 / −1.5 / −1.5 | 0 | +3.19 / +4.44 / +3.26 | +0.65 / +0.62 / +0.67 | rejected |
| C, D — milder variants | ≈ −14 | ≤ −1.5 | 0 | +0.35 … +2.23 | +0.55 … +0.93 | rejected |
| **E = `RVS-VOICE-MASTER-v1`** | −13.9 / −14.0 / −13.8 | −3.1 / −1.5 / −1.8 | **0** | **−2.74 / −0.42 / −0.28** | +0.68 / +0.77 / +0.90 | **accepted** |
LRA stays 1.1–1.4 LU (TTS is already dense; compression only evens chunk-to-chunk levels). Acceptance rule met: loudness within ±0.2 LU of target, true peak ≤ −1.5 dBTP (QA ceiling −1.0), zero clipping, sibilance not increased. Also MEASURED: `loudnorm` without a following `aformat` outputs **192 kHz** on FFmpeg 6.1.1 (v5.0 said 96 kHz) — the `aformat=48000` lock stays mandatory; the double-reverse silence trim kept the voiced span within ±10 ms (no word cut). **Subjective quality is NOT measured — NEEDS-HUMAN (O.6).**

### O.3 Primary HQ LOCAL engine — Kokoro-82M via `kokoro-onnx` (decision record, CN-001)
- Candidates searched (2 Nov 2026): Kokoro-82M (Apache-2.0 weights, 7,327 likes, 11.4 M downloads/month, Hindi voices grade C upstream), Piper (code `OHF-Voice/piper1-gpl` GPL-3.0; Hindi voices `pratham`/`priyamvada` dataset CC BY-NC-SA 4.0, `rohan` IIT-M IndicTTS licence → NOT-OPEN), `resemble-ai/chatterbox` (MIT, Hindi, but torch → Reject List), `ai4bharat/IndicF5` (151★ → bar fail), XTTS-v2 / Fish-Speech / F5-TTS (non-commercial weights → NOT-OPEN, not adopted), MeloTTS / Parler-TTS (no Hindi). **Winner: Kokoro-82M** — only qualified, commercially usable, CPU-only (ONNX Runtime, no torch) Hindi engine.
- **MEASURED (4 vCPU x86-64):** fp32 model `kokoro-v1.0.onnx` 325,532,387 B (sha256 `7d5df8ec…6a6c5`) + `voices-v1.0.bin` 28,214,398 B (sha256 `bca610b8…bf7d`), RTF 0.348–0.365, model load 1.05–2.76 s, peak RSS 680–697 MB, 24 kHz mono output. Termux/ARM: NOT-RUN (onnxruntime availability on Termux must be confirmed by `--bench`; if absent, Termux uses `edge-tts` → `espeak-ng`).
- Setup (RP-1/PC, once): `pip install -r requirements.txt`; download both files into `assets/models/` from the Hugging Face mirror `fastrtc/kokoro-onnx` (or the upstream GitHub release) and verify the sha256 above; or set `RVS_KOKORO_MODEL`/`RVS_KOKORO_VOICES`. Voices: `hm_omega` (default male), `hf_alpha` (female); `lang="hi"` (espeak-ng G2P inside `kokoro-onnx`).

### O.4 Optional Premium Voice Path (DEC-02, HIGH-IMPACT; default OFF)
- Provider: **ElevenLabs** `eleven_multilingual_v2` (Hindi supported per official models page; 10,000 chars/request), API `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000`, header `xi-api-key` (VERIFIED-LIVE 2 Nov 2026). Price `$0.08 / 1K characters` (API pricing page) → cost model App L.
- **Activation:** only when `RVS_PREMIUM_TTS=on` **and** `ELEVENLABS_API_KEY` is present (env or `.env`); key present + toggle off → `RVS_WARN_046`, premium not used. Normalizer before, `RVS-VOICE-MASTER-v1` after, same as every engine.
- **Failure:** 401/403 → `RVS_WARN_042`; 429/quota → `RVS_WARN_044`; timeout/5xx/network → `RVS_WARN_045`; each falls back to the default chain for the whole run.
- **Privacy disclosure:** when ON, the normalised `say` text of every chunk (script narration only — no keys, no file paths, no research dossier) is sent to ElevenLabs servers; Operator must accept ElevenLabs' terms. Offline-first default is unchanged.
- **Undo:** delete `ElevenLabsPremium` from `voice_engines.py`, the 4 `RVS_*ELEVENLABS*`/`RVS_PREMIUM_TTS` variables, D17 and this section.

### O.5 Voice tests (wired into App N)
`TC-35` (chain loudness/true peak/48 kHz — pytest, MEASURED pass), `TC-28` (engine fallback + consistency — MEASURED: chain falls to `kokoro-onnx` when `edge-tts` is absent), `TC-33` (premium failures — mocked HTTP, NOT-RUN in audit), `TC-14` (normalizer), silence-trim word-safety (O.2 measurement), narration duration vs `target_sec` (`RVS_WARN_120`).

### O.6 Human listening checklist (NEEDS-HUMAN — the AI cannot hear)
Listen to the first 60 s of `final_master_16x9.mp4` on phone speaker **and** earphones:
1. **Clarity** — every Hindi/Hinglish word understandable without captions?
2. **Warmth** — voice full, not thin/tinny?
3. **Harshness / sibilance** — any piercing "s/sh" or hiss?
4. **Pumping / breathing** — volume breathing between words or under BGM?
5. **Naturalness** — Hindi numbers (`साढ़े तीन`), English words inside Hindi, schwa deletion sound right?
6. **Consistency** — same voice, level and tone across all chapters and derived clips?
Any "no" → note the timestamp; switch `RVS_VOICE_MASTER=safe`/`off` or another voice and re-render.
