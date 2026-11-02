# Voice lab (module M1) — MEASURED 2026-11-02 on this audit VM (4 vCPU, 15 GiB RAM, Linux x86_64, FFmpeg 6.1.1)
Engine: kokoro-onnx 0.6.1 (PyPI, isolated uv venv voice_lab/.venv_kokoro), model kokoro-v1.0.onnx (fp32, 325,532,387 B, sha256 7d5df8ec…6a6c5, from HF fastrtc/kokoro-onnx), voices-v1.0.bin (sha256 bca610b8…bf7d). Hindi voices hf_alpha (F), hm_omega (M), hm_psi (M); lang="hi" (espeak-ng G2P).
Bench: RTF 0.348–0.365 (synth_sec/audio_sec), model load 1.05–2.76 s, peak RSS 680–697 MB, output 24 kHz mono. (kokoro_bench.jsonl)
Test texts: generic Hindi sentences written for the audit (not PRD content); clip 3 dense in sibilants + numbers.
Chains (all followed by two-pass loudnorm I=-14:TP=-1.5:LRA=11 linear + aformat 48k stereo):
- base: none (PRD v5.0 behaviour)
- A (prompt hypothesis): bass=g=4:f=110,treble=g=2,compand=… → sibilance 5–9 kHz +2.56..+3.03 dB vs base → REJECTED
- B: highpass+equalizer warmth/presence+deesser+acompressor+alimiter → sibilance +3.19..+4.44 dB → REJECTED
- C, D: partial (sibilance +0.35..+2.23 dB) → REJECTED
- E (ACCEPTED = RVS-VOICE-MASTER-v1): highpass=f=70:poles=2,lowshelf=f=160:g=3,equalizer=f=3000:t=q:w=1.0:g=1.0,highshelf=f=6000:g=-4,deesser=i=0.6:m=0.5:f=0.5:s=o,acompressor=threshold=-20dB:ratio=2:attack=10:release=150:makeup=1:knee=4,alimiter=limit=0.89:attack=5:release=50:level=disabled
  E results: I = -13.9/-14.0/-13.8 LUFS; TP = -3.1/-1.5/-1.8 dBTP; LRA 1.1/1.2/1.4 LU; clipped samples 0/0/0; sibilance 5–9 kHz −2.74/−0.42/−0.28 dB vs base; <250 Hz warmth +0.68/+0.77/+0.90 dB; 2–4 kHz presence +0.70/+0.36/−0.04 dB.
  base results: I -13.8/-14.0/-14.0, TP -1.6/-1.5/-1.5, LRA 1.3/1.2/1.3, 0 clipped.
Silence trim (PRD double-reverse silenceremove @ -45 dB) on 300 ms/400 ms padded clips: voiced span preserved (11525→11530 ms, 12215→12225 ms; ±10 ms = probe frame granularity) → no word cut.
loudnorm native output sample rate (no aformat after) = 192000 Hz on FFmpeg 6.1.1 (PRD says 96000 Hz → corrected).
Not measured: edge-tts (would send text to Microsoft service — audit confidentiality rule), Termux/ARM RTF (no device), subjective quality (NEEDS-HUMAN).
Piper Hindi voices (rhasspy/piper-voices hi_IN pratham/priyamvada: dataset CC BY-NC-SA 4.0; rohan: IIT-M IndicTTS licence) → NOT-OPEN for monetized use → Piper not eligible for Hindi.
