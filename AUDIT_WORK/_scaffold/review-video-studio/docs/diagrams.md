## Appendix Q — Visual Architecture (Mermaid, v5.1, addition H)
*(Drawn last from the final tables. Tables/sections stay the source of truth; each diagram names the section it mirrors. Max 25 nodes per diagram. Validated with `@mermaid-js/mermaid-cli` in the audit — result in Appendix N.5 / audit report.)*

**Q.1 System architecture & context** (mirrors §3, §7.1, Hard Rule 1, App H)
```mermaid
flowchart LR
  OP[Operator] -->|commands, posters, transcripts| SK[Skill review-video-studio]
  OP -->|PR-01..04/09| RAI[Research AI app]
  OP -->|PR-05/06/07/10A| GEM[Gemini app]
  SK -->|S7-L| VP[voice_pack.py]
  VP --> VE[voice_engines.py]
  VE -->|network exception a| EDGE[edge-tts online]
  VE -->|network exception b, default OFF| EL[ElevenLabs premium]
  VE --> KO[kokoro-onnx local]
  VE --> ES[espeak-ng floor]
  SK -->|S8-L| CO[character_overlay.py]
  SK -->|S8-L/S12| BV[build_video.py]
  BV --> FF[FFmpeg + libass]
  SK -->|S9-L/S13| QA[qa_contact_sheet.py]
  SK -->|S11-S13| RS[repurpose_shorts.py]
  ALL[rvs_common.py] -.->|logs, codes, secrets| LOGS[(logs/run_id.jsonl)]
  ENV[(.env / OS env)] -.-> ALL
```
Legend: solid = data/control flow; dotted = shared helper/config; `(…)` = file store. Only `EDGE` and `EL` touch the network at runtime.

**Q.2 End-to-end pipeline** (mirrors §5.1 + gates)
```mermaid
flowchart TD
  S0[S0 Intake] --> S1[S1 Topic Lock / Trend Radar] --> G1{G1 LOCK TOPIC}
  G1 --> S2[S2 Mission Pack] --> S3[S3 Data QC + Digest]
  S3 -->|density < 85 wpm| PR07[PR-06 / PR-07 fallback] --> S3
  S3 --> S4[S4 Insight Brief + Runtime] --> G2{G2 LOCK RUNTIME}
  G2 --> S5[S5-L Chapter Script] --> S6[S6-L Visual Plan] --> G34{G3/G4 APPROVE SCRIPT}
  G34 --> S7[S7-L Preflight + Voice] --> S8[S8-L Master Render]
  S8 --> S9[S9-L 16-Pt QA]
  S9 -->|RVS_ERR_060| S8
  S9 --> S10[S10-L YouTube Pack] --> G5{G5-L CUT SHORTS}
  G5 --> S11[S11 Moment Mining] --> S12[S12 Derived Edits] --> S13[S13 Shorts QA + Packs] --> G6{G6-S SHORTS OK}
```
Legend: rectangles = stages, diamonds = Operator gates; red-path labels are error codes (Appendix J).

**Q.3 Render paths** (mirrors §7.1 table)
```mermaid
flowchart LR
  PF[preflight.py] -->|ffmpeg + fonts + TTS ok| RP1[RP-1 full cloud build]
  PF -->|render ok, TTS blocked| RP2[RP-2 hybrid]
  PF -->|is_termux| RP3[RP-3 Termux kit, 1080p only]
  PF -->|ffmpeg/filters/fonts missing| RP4[RP-4 manual CapCut/VN]
  RP2 --> A[S7-L.a run_voice_only.sh on phone] --> B[S7-L.b attach voice_pack.zip] --> RENDER[build_video.py in cloud]
  RP1 --> RENDER
  RP3 --> FULL[run_full_render.sh]
```
Legend: edge labels = preflight conditions (G.1 `probe_environment`).

**Q.4 Repurpose engine** (mirrors §5.4, G.8)
```mermaid
flowchart LR
  W[(words.json)] --> MM[mine_moments S11]
  SP[(spec.json)] --> MM
  MM -->|score >= 75, dedupe > 50% overlap| SEL[M-01..M-05]
  MM -->|< 2 strong: RVS_WARN_118| SEL
  SEL --> DS[build_derived_short_spec]
  DS --> AU[assemble_derived_audio]
  VM[(voice_master.wav)] -->|slice + 15 ms fades| AU
  AU -->|2 fresh TTS chunks| VP2[voice_pack hook + CTA]
  AU --> BV2[build_video.py 1080x1920] --> QA2[qa_contact_sheet.py] --> PK[Reel Pack + Short Pack]
```
Legend: `(…)` = files; body audio is never re-synthesised.

**Q.5 Skill router & dependency map** (mirrors App A.3 router, App P.3)
```mermaid
flowchart TD
  SKILL[SKILL.md router] --> REF1[prompts.md]
  SKILL --> REF2[analysis-playbook.md]
  SKILL --> REF3[script-playbook.md]
  SKILL --> REF4[style-packs.md]
  SKILL --> REF5[brand-and-character-kit.md]
  SKILL --> REF6[upload-pack.md]
  K01[OSS-SKL-01 TTS sync] --> K11[OSS-SKL-11 voice master]
  K02[OSS-SKL-02 pipeline] --> K03[OSS-SKL-03 captions]
  K02 --> K04[OSS-SKL-04 palette + cards]
  K02 --> K05[OSS-SKL-05 loudnorm]
  K06[OSS-SKL-06 co-host] --> K02
  K07[OSS-SKL-07 repurpose] --> K01
  K07 --> K02
  K08[OSS-SKL-08 originality] --> REF3
  K09[OSS-SKL-09 schema + QA] --> K02
  K12[OSS-SKL-12 ops layer] -.-> K01
  K12 -.-> K02
  K13[OSS-SKL-13 tests/evals/CI] -.-> K09
```
Legend: arrow = "uses"; dotted = cross-cutting support.

**Q.6 Error handling, retry & fallback** (mirrors §10, App J)
```mermaid
flowchart TD
  CALL[run_cmd / engine call] -->|ok| NEXT[next step]
  CALL -->|edge-tts fails x3| SW[switch whole run to next engine RVS_WARN_041]
  SW --> CALL
  CALL -->|all engines fail| E40[RVS_ERR_040 exit 40]
  CALL -->|timeout| E70[RVS_ERR_070 exit 70]
  CALL -->|ffmpeg rc != 0| E50[RVS_ERR_050 exit 50]
  CALL -->|voice chain filter error| FB[safe chain then bypass RVS_WARN_053] --> NEXT
  NEXT --> QAQ{QA hard checks}
  QAQ -->|fail| E60[RVS_ERR_060 exit 60]
  QAQ -->|pass with warnings| W10[exit 10]
  QAQ -->|pass| OK0[exit 0]
  E40 --> CR[crash_report + resume hint]
  E50 --> CR
  E70 --> CR
```
Legend: `RVS_ERR_*` fatal, `RVS_WARN_*` fail-soft; resume = rerun the same command (engine-keyed cache + scene cache).

**Q.7 Secrets & configuration load order** (mirrors App H)
```mermaid
sequenceDiagram
  participant S as Script main_wrapper
  participant OS as OS environment
  participant E as .env file
  participant P as preflight
  participant V as voice_engines
  S->>OS: read variables first
  S->>E: load_env_file (never overrides OS)
  E-->>S: chmod check (RVS_WARN_043 if not 600)
  S->>P: secret_status prints present/missing only
  P-->>S: RVS_WARN_046/047/048 on mismatch
  S->>V: premium only if RVS_PREMIUM_TTS=on AND key present
  V-->>S: logs pass through redact()
```
Legend: no key value is ever printed, logged, put in prompts or written to files.

**Q.8 CI pipeline & eval flow** (mirrors App M, App N.4)
```mermaid
flowchart LR
  PUSH[push / PR / weekly cron] --> T[job test: py 3.11-3.13]
  T --> C1[compileall] --> C2[shellcheck] --> C3[pytest -m not needs_network] --> C4[run_evals.py recorded] --> C5[cost_model --check]
  PUSH --> D[job diagrams: mermaid-cli]
  MAN[workflow_dispatch + human approval] --> LIVE[job live-evals: --live --model id]
  LIVE --> BASE{baseline change?}
  BASE -->|yes| PR[human-approved PR]
```
Legend: default CI uses recorded fixtures, no network, no keys.
