# QA report — PASS

Video: `king-tu-mil-jaaye.mp4` · 207.1s · voice timing: exact (edge-tts WordBoundary)

| check | result | value | rule |
|---|---|---|---|
| duration_vs_target | PASS | 207.1 | |207.1s − 215s| ≤ 21.5s (fix the SCRIPT, not the speed) |
| distinct_frame_designs | PASS | 15 | ≥ 5 distinct archetype layouts |
| no_repeat_consecutive_layout | PASS | [] | no archetype twice in a row |
| archetype_reuse_limit | PASS | {} | no archetype more than 7× per video |
| designed_transitions | PASS | 21 | every scene boundary has a designed transition (no hard cuts) |
| text_min_size | PASS | [] | hero ≥56px, body ≥40px, label ≥30px |
| caption_size | PASS | 68 | captions ≥ 64px on a 1080px-wide frame |
| caption_collision | PASS | [] | scene text ends above the caption band when captions are on |
| safe_zones | PASS | [] | critical text inside Reels safe area (top 225, bottom 1495, right 1000 below y=1000) |
| no_static_runs | PASS | {"longest_s": 2.3, "at_s": 90.2} | a visible visual event (≥0.4 % of pixels change) at least every 2.5 s |
| hook_pattern_interrupt | PASS | 100.0 | ≥ 20 % of the frame changes inside the first 1.5 s |
| hook_not_greeting | PASS | "Romantic gaana… aur pehle 30 second mein" | first line is a hook, never a greeting |
| hook_layout | PASS | "hook_slam" | opening beat uses a designed hook |
| visually_distinct_frames | PASS | 16 | ≥ 5 visually different scene frames (dHash > 10 bits) |
| no_banding_or_flat_fills | PASS | 0.228 | flat 4×4 plateaus < 25 % of mid-tone area |
| dead_space | PASS | {"max": 0.31, "per_scene": [0.056, 0.105, 0.128, 0.085, 0.049, 0.024, 0.045, 0.3 | featureless area ≤ 55 % of the safe area |
| loudness | PASS | {"I": -14.07, "TP": -1.74, "LRA": 2.5} | −14 LUFS ±1.5, true peak ≤ −0.8 dBTP |
| music_present | PASS | -33.2 | music bed present by default |
| sfx_on_events | PASS | 91 | SFX on transitions + in-scene events |
| captions_cover_speech | PASS | "458/458" | every spoken word in caption beats is captioned (word-synced) |
| script_cliches | PASS | [] | ≤ 1 cliché per script (specific > generic) |
| dna_differs_from_past | PASS | [] | ≥ 4 of 12 style dimensions differ from each of the last 5 videos |

Self-review is still required: open the contact sheet + frames, then write review.md (see SKILL.md).