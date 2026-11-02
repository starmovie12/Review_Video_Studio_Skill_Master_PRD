"""character_overlay.py — event-driven 2D co-host rig, RMS lip-sync, ffconcat timeline (File 22, PRD v5.1 App G.7, OSS-SKL-06).
Own design (NONE-FOUND qualified OSS); patterns studied: Open-LLM-VTuber (volume→mouth, emotion tags) and Rhubarb Lip Sync
(in-between mouth smoothing). Character Asset Rights Gate (§7.11.3, DEC-04): third-party presets render only when
spec.character.asset_rights ∈ {licensed, original_owned, permission_granted}; otherwise CHAR-RVS-ORIGINAL is drawn (RVS_WARN_083).
CLI: python scripts/character_overlay.py --spec spec.json --words words.json --voice voice_master.wav --work WORK [--fps 30]
"""
import argparse
import json
import math
import os
import sys
import wave
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402

from rvs_common import RvsError, SKILL_ROOT, log_event, main_wrapper, stage_end, stage_start, warn  # noqa: E402

THIRD_PARTY_PRESETS = {"CHAR-GOJO-HOST", "CHAR-L-DETECTIVE", "CHAR-CONAN-SLEUTH"}
RIGHTS_OK = {"licensed", "original_owned", "permission_granted"}
LATIN_FONT = str(SKILL_ROOT / "assets" / "fonts" / "Poppins-Bold.ttf")


def resolve_preset(char_cfg: dict) -> str:
    """Asset Rights Gate: returns the preset that may legally be drawn (decision DEC-04; legal review = NEEDS-HUMAN)."""
    preset = char_cfg.get("preset_id", "CHAR-RVS-ORIGINAL")
    if preset in THIRD_PARTY_PRESETS and char_cfg.get("asset_rights", "undeclared") not in RIGHTS_OK:
        warn("RVS_WARN_083", "S8-L", f"{preset} without declared asset_rights → CHAR-RVS-ORIGINAL rendered")
        return "CHAR-RVS-ORIGINAL"
    return preset

ANIME_HOST_PRESETS = {
    "CHAR-GOJO-HOST": {
        "name": "GOJO SENSEI",
        "hair": "#F8FAFC",
        "hair_shadow": "#CBD5E1",
        "skin": "#FFE4D6",
        "skin_shadow": "#F3C6B6",
        "jacket": "#0B0F19",
        "collar_trim": "#FFD13B",
        "shades": "#05070E",
        "eyes_glow": "#00F5D4",
        "aura": "#38BDF8",
    },
    "CHAR-RVS-ORIGINAL": {
        "name": "RVS HOST",
        "hair": "#1F2937",
        "hair_shadow": "#111827",
        "skin": "#F1C9A5",
        "skin_shadow": "#D9A982",
        "jacket": "#0F172A",
        "collar_trim": "#38BDF8",
        "shades": "#0B1020",
        "eyes_glow": "#38BDF8",
        "aura": "#38BDF8",
    },
    "CHAR-L-DETECTIVE": {
        "name": "DETECTIVE L",
        "hair": "#111827",
        "hair_shadow": "#030712",
        "skin": "#F8FAFC",
        "skin_shadow": "#E2E8F0",
        "jacket": "#E2E8F0",
        "collar_trim": "#64748B",
        "shades": "#1E293B",
        "eyes_glow": "#FACC15",
        "aura": "#94A3B8",
    },
    "CHAR-CONAN-SLEUTH": {
        "name": "SLEUTH CONAN",
        "hair": "#292524",
        "hair_shadow": "#1C1917",
        "skin": "#FFE4D6",
        "skin_shadow": "#F3C6B6",
        "jacket": "#1D4ED8",
        "collar_trim": "#EF4444",
        "shades": "#F8FAFC",
        "eyes_glow": "#38BDF8",
        "aura": "#60A5FA",
    },
}

MOUTH_STATES = ("closed", "half", "open", "wide")
EYE_STATES = ("open", "blink")
EXPRESSIONS = (
    "neutral", "thinking", "hyped", "shocked", "roast", "verdict_salute",
    "confident_smirk", "surprise_shock", "serious_sarcastic",
    "comparison_thinking", "verdict_unlimited", "outro_salute",
)
GOJO_CUES = (
    "none", "hook_entry", "surprise_reaction", "analysis_serious",
    "comparison_pose", "verdict_confident", "outro_signature",
)
GOJO_POWERS = ("none", "infinity", "blue", "red", "hollow_purple", "six_eyes")

POWER_RGB = {
    "blue": (0, 180, 216),
    "red": (255, 42, 84),
    "hollow_purple": (157, 78, 221),
    "six_eyes": (0, 245, 212),
    "infinity": (56, 189, 248),
    "none": (56, 189, 248),
}

def CueToPowerAndExpr(gojo_cue: str, fallback_expr: str = "neutral", fallback_power: str = "none") -> tuple[str, str]:
    """Maps a high-level gojo_cue to its default expression and Cursed Energy power effect."""
    mapping = {
        "hook_entry": ("confident_smirk", "blue"),
        "surprise_reaction": ("surprise_shock", "six_eyes"),
        "analysis_serious": ("serious_sarcastic", "red"),
        "comparison_pose": ("comparison_thinking", "infinity"),
        "verdict_confident": ("verdict_unlimited", "hollow_purple"),
        "outro_signature": ("outro_salute", "infinity"),
    }
    def_expr, def_pwr = mapping.get(gojo_cue, (fallback_expr, fallback_power))
    expr = fallback_expr if fallback_expr != "neutral" else def_expr
    pwr = fallback_power if fallback_power != "none" else def_pwr
    return expr, pwr

def apply_studio_rim_and_bloom(fg_rgba: Image.Image, power: str) -> Image.Image:
    """Applies a 24px Volumetric Cursed-Energy Back-Glow Rim Light + 14px Contact Drop-Shadow to any cutout or rig frame."""
    w, h = fg_rgba.size
    r, g, b = POWER_RGB.get(power, (56, 189, 248))
    alpha = fg_rgba.split()[3]

    # 1. Soft dark contact drop-shadow (+8px, +12px)
    shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=14))
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", (w, h), (4, 6, 14, 180))
    shadow_layer.putalpha(shadow_alpha)
    shadow.paste(shadow_layer, (8, 12))

    # 2. Volumetric Cursed-Energy Rim Glow around silhouette
    glow_alpha = alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(radius=18))
    rim_glow = Image.new("RGBA", (w, h), (r, g, b, 0))
    rim_glow.putalpha(glow_alpha)

    comp = Image.alpha_composite(shadow, rim_glow)
    comp = Image.alpha_composite(comp, fg_rgba)
    shadow.close()
    shadow_layer.close()
    rim_glow.close()
    return comp

def draw_anime_reviewer_sprite(
    preset_id: str,
    expression: str,
    eye_state: str,
    mouth_state: str,
    size_px: int = 420,
    power: str = "infinity",
) -> Image.Image:
    """Renders Gojo Co-Host on a Frosted Glassmorphic HUD Medallion with Volumetric Gaussian Bloom & Multi-Shaded Layers."""
    p = ANIME_HOST_PRESETS.get(preset_id, ANIME_HOST_PRESETS["CHAR-GOJO-HOST"])
    r_pwr, g_pwr, b_pwr = POWER_RGB.get(power, (56, 189, 248))
    base = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    cx, cy = size_px // 2, size_px // 2
    bounce_y = -6 if mouth_state in ("open", "wide") else 0

    # 1. Volumetric Gaussian-Bloomed Cursed Energy Corona (Outer + Inner Glow)
    bloom = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom)
    bd.ellipse([22, 30 + bounce_y, size_px - 22, size_px - 16 + bounce_y], fill=(r_pwr, g_pwr, b_pwr, 155))
    if power == "hollow_purple":
        # Colliding Blue (left) + Red (right) energy spheres merging into Hollow Purple core
        bd.ellipse([18, cy - 20 + bounce_y, 126, cy + 88 + bounce_y], fill=(0, 180, 216, 210))
        bd.ellipse([size_px - 126, cy - 20 + bounce_y, size_px - 18, cy + 88 + bounce_y], fill=(255, 42, 84, 210))
        bd.ellipse([36, cy + 12 + bounce_y, 138, cy + 114 + bounce_y], fill=(224, 170, 255, 240))
    elif power in ("blue", "red", "six_eyes"):
        orb_x = 34 if power != "red" else size_px - 126
        bd.ellipse([orb_x, cy + 16 + bounce_y, orb_x + 92, cy + 108 + bounce_y], fill=(r_pwr, g_pwr, b_pwr, 235))
    bloom = bloom.filter(ImageFilter.GaussianBlur(radius=22))
    base = Image.alpha_composite(base, bloom)
    bloom.close()

    # 2. Frosted Dark-Glass HUD Medallion Ring
    fg = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    d.ellipse([28, 36 + bounce_y, size_px - 28, size_px - 22 + bounce_y], fill=(10, 14, 26, 230), outline=(r_pwr, g_pwr, b_pwr, 255), width=5)
    d.ellipse([34, 42 + bounce_y, size_px - 34, size_px - 28 + bounce_y], outline=(255, 255, 255, 70), width=1)

    # 3. Cel-Shaded Jujutsu High-Collar Jacket & Torso
    d.polygon(
        [(cx - 126, size_px - 28), (cx - 88, cy + 42 + bounce_y), (cx + 88, cy + 42 + bounce_y), (cx + 126, size_px - 28)],
        fill=p["jacket"], outline=p["collar_trim"],
    )
    d.rectangle([cx - 56, cy + 20 + bounce_y, cx + 56, cy + 68 + bounce_y], fill=p["jacket"], outline=p["collar_trim"], width=3)

    # 4. Dual-Shaded Anime Face (Main Lit Plane + Cel-Shadow Jaw Plane)
    face_top = cy - 96 + bounce_y
    face_bot = cy + 58 + bounce_y
    d.polygon(
        [(cx - 78, face_top + 35), (cx + 78, face_top + 35), (cx + 68, face_bot - 26), (cx, face_bot), (cx - 68, face_bot - 26)],
        fill=p["skin"], outline="#1E293B",
    )
    d.polygon(
        [(cx, face_top + 35), (cx + 78, face_top + 35), (cx + 68, face_bot - 26), (cx, face_bot)],
        fill=p["skin_shadow"],
    )

    # 5. Multi-Layered Spiky Snow-White Gojo Hair (Shadow Under-Crown + Lit Spikes)
    shadow_spikes = [
        (cx - 114, face_top + 42), (cx - 95, face_top - 24), (cx - 52, face_top + 12),
        (cx - 38, face_top - 48), (cx, face_top - 4), (cx + 38, face_top - 48),
        (cx + 56, face_top + 12), (cx + 96, face_top - 22), (cx + 114, face_top + 42),
    ]
    d.polygon(shadow_spikes, fill=p["hair_shadow"])
    spikes = [(x, y - 5) for x, y in shadow_spikes]
    d.polygon(spikes, fill=p["hair"], outline="#0F172A")

    # 6. Glowing Cyan Six-Eyes Unveil + Blindfold/Shades Slide-Down
    eye_y = cy - 24 + bounce_y
    is_gojo = preset_id == "CHAR-GOJO-HOST"
    six_eyes_unveiled = is_gojo and expression in ("surprise_shock", "verdict_unlimited", "shocked", "verdict_salute", "hyped") or power in ("six_eyes", "hollow_purple")
    if eye_state == "blink" and not six_eyes_unveiled:
        d.line([(cx - 52, eye_y), (cx - 18, eye_y)], fill="#0F172A", width=5)
        d.line([(cx + 18, eye_y), (cx + 52, eye_y)], fill="#0F172A", width=5)
    else:
        d.ellipse([cx - 54, eye_y - 16, cx - 16, eye_y + 16], fill="#00F5D4", outline="#FFFFFF", width=3)
        d.ellipse([cx + 16, eye_y - 16, cx + 54, eye_y + 16], fill="#00F5D4", outline="#FFFFFF", width=3)
        d.ellipse([cx - 41, eye_y - 6, cx - 29, eye_y + 6], fill="#FFFFFF")
        d.ellipse([cx + 29, eye_y - 6, cx + 41, eye_y + 6], fill="#FFFFFF")

    shade_offset = 22 if six_eyes_unveiled else 0
    sy = eye_y + shade_offset
    d.ellipse([cx - 58, sy - 16, cx - 14, sy + 16], fill=p["shades"], outline="#FFD13B", width=3)
    d.ellipse([cx + 14, sy - 16, cx + 58, sy + 16], fill=p["shades"], outline="#FFD13B", width=3)
    d.line([(cx - 14, sy), (cx + 14, sy)], fill="#FFD13B", width=3)

    # 7. 4-State Lip-Sync Mouth Viseme
    my = cy + 28 + bounce_y
    if mouth_state == "closed":
        if expression in ("serious_sarcastic", "roast"):
            d.line([(cx - 18, my + 2), (cx + 18, my + 2)], fill="#0F172A", width=4)
        else:
            d.line([(cx - 20, my + 2), (cx + 4, my + 4), (cx + 22, my - 5)], fill="#0F172A", width=4)
    elif mouth_state == "half":
        d.rounded_rectangle([cx - 18, my - 6, cx + 18, my + 8], radius=6, fill="#7F1D1D", outline="#0F172A", width=3)
    elif mouth_state == "open":
        d.rounded_rectangle([cx - 24, my - 10, cx + 24, my + 16], radius=10, fill="#991B1B", outline="#0F172A", width=3)
        d.rectangle([cx - 18, my - 8, cx + 18, my - 2], fill="#FFFFFF")
    else:
        d.ellipse([cx - 28, my - 14, cx + 28, my + 22], fill="#DC2626", outline="#0F172A", width=3)
        d.rectangle([cx - 20, my - 11, cx + 20, my - 3], fill="#FFFFFF")

    # 8. Hand Gestures & Active Cursed Technique HUD Nameplate
    if expression in ("verdict_unlimited", "verdict_salute"):
        d.rounded_rectangle([size_px - 118, cy + 45 + bounce_y, size_px - 36, cy + 140 + bounce_y], radius=10, fill="#FFD13B", outline="#0F172A", width=3)
        sx, sy0 = size_px - 77, cy + 70 + bounce_y
        star = [(0, -16), (5, -5), (16, -5), (7, 2), (10, 14), (0, 7), (-10, 14), (-7, 2), (-16, -5), (-5, -5)]
        d.polygon([(sx + px, sy0 + py) for px, py in star], fill="#0F172A")

    d.rounded_rectangle([cx - 122, size_px - 52, cx + 122, size_px - 12], radius=14, fill=(11, 13, 19, 240), outline=(r_pwr, g_pwr, b_pwr, 255), width=3)
    label = f"{p['name']} • {power.upper()}" if power != "none" else p["name"]
    try:
        f_lbl = ImageFont.truetype(LATIN_FONT, max(12, size_px // 22))
    except OSError:
        f_lbl = ImageFont.load_default()
    d.text((cx - 98, size_px - 42), label[:22], fill="#FFFFFF", font=f_lbl)

    combined = Image.alpha_composite(base, fg)
    base.close()
    fg.close()
    return apply_studio_rim_and_bloom(combined, power)

def ensure_anime_character_sprites(
    work_dir: str, preset_id: str = "CHAR-GOJO-HOST", custom_dir: str = "", size_px: int = 420
) -> dict[tuple[str, str, str, str], str]:
    """Builds or loads the cached RGBA sprite table (wrapping any custom PNGs in studio rim-light & drop-shadow)."""
    sprite_dir = os.path.join(work_dir, f"sprites_{preset_id}_{size_px}")
    os.makedirs(sprite_dir, exist_ok=True)
    sprite_map = {}

    blank_path = os.path.join(sprite_dir, "spr_blank.png")
    if not os.path.exists(blank_path):
        Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0)).save(blank_path)
    sprite_map[("none", "open", "closed", "none")] = blank_path

    active_combos = [
        ("confident_smirk", "blue"),
        ("surprise_shock", "six_eyes"),
        ("serious_sarcastic", "red"),
        ("comparison_thinking", "infinity"),
        ("verdict_unlimited", "hollow_purple"),
        ("outro_salute", "infinity"),
        ("neutral", "infinity"),
        ("thinking", "infinity"),
        ("hyped", "six_eyes"),
        ("shocked", "six_eyes"),
        ("roast", "red"),
        ("verdict_salute", "hollow_purple"),
    ]
    required = ["closed", "half", "open", "wide", "blink"]
    if custom_dir:
        missing = [m for m in required if not os.path.exists(os.path.join(custom_dir, f"{m}.png"))]
        if missing:
            warn("RVS_WARN_054", "S8-L", f"custom sprites missing {missing} → procedural rig for ALL frames (no mixing)")
            custom_dir = ""
    for expr, pwr in active_combos:
        for eye in EYE_STATES:
            for mouth in MOUTH_STATES:
                fname = f"spr_{expr}_{pwr}_{eye}_{mouth}.png"
                fpath = os.path.join(sprite_dir, fname)
                if custom_dir and os.path.exists(os.path.join(custom_dir, f"{mouth}.png")):
                    with Image.open(os.path.join(custom_dir, f"{mouth}.png")) as raw_c:
                        cutout = raw_c.convert("RGBA").resize((size_px, size_px), Image.Resampling.LANCZOS)
                        lit = apply_studio_rim_and_bloom(cutout, pwr)
                        lit.save(fpath)
                        cutout.close()
                        lit.close()
                elif not os.path.exists(fpath):
                    im = draw_anime_reviewer_sprite(preset_id, expr, eye, mouth, size_px, pwr)
                    im.save(fpath)
                    im.close()
                sprite_map[(expr, eye, mouth, pwr)] = fpath
    return sprite_map

def compute_lipsync_rle_timeline(
    voice_wav_path: str, words_data: dict, spec: dict, work_dir: str, fps: int = 30, size_px: int = 420
) -> str:
    """Analyzes voice_master.wav RMS decibels at 30fps and builds an event-driven RLE FFmpeg concat file (char_timeline.txt)."""
    char_cfg = spec.get("character", {"enabled": True, "preset_id": "CHAR-RVS-ORIGINAL"})
    preset_id = resolve_preset(char_cfg)
    sprite_map = ensure_anime_character_sprites(work_dir, preset_id, char_cfg.get("custom_sprite_dir", ""), size_px)
    blank_sprite = sprite_map[("none", "open", "closed", "none")]

    spec_chunks_by_id = {c["chunk_id"]: c for c in spec.get("chunks", [])}
    chunk_windows = []
    total_chunks = len(words_data["chunks"])
    for idx, chk in enumerate(words_data["chunks"]):
        sc_chk = spec_chunks_by_id.get(chk["chunk_id"], {})
        cue = chk.get("gojo_cue") or sc_chk.get("gojo_cue")
        if not cue:
            if idx == 0:
                cue = "hook_entry"
            elif idx == total_chunks - 1:
                cue = "verdict_confident"
            elif chk.get("expression") in ("shocked", "surprise_shock"):
                cue = "surprise_reaction"
            elif chk.get("expression") in ("roast", "serious_sarcastic"):
                cue = "analysis_serious"
            elif chk.get("expression") in ("thinking", "comparison_thinking"):
                cue = "comparison_pose"
            else:
                cue = "none"
        raw_expr = chk.get("expression") or sc_chk.get("expression", "neutral")
        raw_pwr = chk.get("gojo_power") or sc_chk.get("gojo_power", "none")
        expr, pwr = CueToPowerAndExpr(cue, raw_expr, raw_pwr)
        chunk_windows.append((chk["start_ms"], chk["end_ms"] + chk["pause_after_ms"], cue, expr, pwr))

    frame_states = []
    prev_mouth = "closed"
    with wave.open(voice_wav_path, "rb") as wf:
        sr, n_ch = wf.getframerate(), wf.getnchannels()
        total_video_frames = max(1, int(math.ceil(wf.getnframes() / (sr / float(fps)))))
        win_frames = max(1, int(round(sr / float(fps))))
        for f_idx in range(total_video_frames):
            window = array("h", wf.readframes(win_frames))  # streamed: constant memory for any length (D-145)
            t_ms = int((f_idx / float(fps)) * 1000)
            active_cue, active_expr, active_pwr = "none", "neutral", "infinity"
            for st_ms, et_ms, cue, expr, pwr in chunk_windows:
                if st_ms <= t_ms <= et_ms:
                    active_cue, active_expr, active_pwr = cue, expr, pwr
                    break
            if active_cue == "none":
                frame_states.append(blank_sprite)
                prev_mouth = "closed"
                continue
            if len(window):
                rms = math.sqrt(sum(float(s) * float(s) for s in window) / len(window)) / 32768.0
                db = 20.0 * math.log10(max(1e-6, rms))
            else:
                db = -90.0
            mouth = "closed" if db < -42.0 else "half" if db < -26.0 else "open" if db < -14.0 else "wide"
            if mouth == "closed" and prev_mouth == "wide":
                mouth = "half"  # Rhubarb-style in-between
            prev_mouth = mouth
            eye = "blink" if (f_idx % max(1, int(round(3.4 * fps)))) >= max(1, int(round(3.4 * fps))) - 4 else "open"
            key = (active_expr, eye, mouth, active_pwr)
            frame_states.append(sprite_map.get(key, sprite_map[("confident_smirk", eye, mouth, "blue")]))

    rle_lines = ["ffconcat version 1.0"]
    frame_dur = 1.0 / float(fps)
    curr_path = frame_states[0]
    run_len = 1
    for p in frame_states[1:]:
        if p == curr_path:
            run_len += 1
        else:
            rel_p = os.path.relpath(curr_path, work_dir)
            rle_lines.append(f"file '{rel_p}'")
            rle_lines.append(f"duration {run_len * frame_dur:.6f}")
            curr_path = p
            run_len = 1
    rel_last = os.path.relpath(curr_path, work_dir)
    rle_lines.append(f"file '{rel_last}'")
    rle_lines.append(f"duration {run_len * frame_dur:.6f}")
    rle_lines.append(f"file '{rel_last}'")

    concat_path = os.path.join(work_dir, "char_timeline.txt")
    with open(concat_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rle_lines) + "\n")
    return concat_path


def main():
    ap = argparse.ArgumentParser(description="co-host timeline builder")
    for k in ("spec", "words", "voice", "work"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", type=int, default=420)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    if not spec.get("character", {}).get("enabled", True):
        log_event("INFO", "S8-L", "host_disabled", None, "character.enabled=false — no timeline")
        return None
    stage_start("S8-L-HOST", "co-host timeline")
    p = compute_lipsync_rle_timeline(a.voice, json.load(open(a.words, encoding="utf-8")), spec, a.work, a.fps, a.size)
    stage_end("S8-L-HOST", p)
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S8-L"))
