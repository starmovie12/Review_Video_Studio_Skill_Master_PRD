"""build_video.py — S8-L/S12 render engine (File 18, PRD v5.1 App G.3; OSS-SKL-02/03/04/05/11).
Pipeline: assets → captions.ass → SFX bed → voice mastering + BGM duck + two-pass loudnorm → per-scene resumable
segments (scene_{beat:03d}.mp4, atomic + ffprobe-validated) → concat → host overlay → grade → captions → (UHD upscale)
→ BT.709 matrix + tags → encode. Dependencies: FFmpeg ≥5.1 (libass, libx264, libx265), Pillow ≥10 (raqm optional).
CLI: python scripts/build_video.py --spec spec.json --words words.json --voice voice_master.wav --work WORK --out out.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import wave
from array import array
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, features  # noqa: E402

from rvs_common import (RvsError, SKILL_ROOT, check_disk_space, ffprobe_duration, log_event, main_wrapper,  # noqa: E402
                        run_cmd, stage_end, stage_start, warn)
from voice_engines import VOICE_MASTER_CHAIN_SAFE, voice_master_chain  # noqa: E402

STAR_VECTOR_PATH = "m 24 0 l 31 15 48 18 35 30 39 47 24 38 9 47 13 30 0 18 17 15"
FONTS_DIR = SKILL_ROOT / "assets" / "fonts"
# Cinema grade (single source; style packs only change the four numbers via STYLE_GRADE)
CINEMA_GRADE_FILTER = ("vibrance=intensity=0.28:rbal=1.05:gbal=1.00:bbal=1.08,"
                       "eq=contrast=1.07:brightness=0.01:saturation=1.14:gamma=1.02,"
                       "colorbalance=rs=-0.03:gs=-0.01:bs=0.05:rh=0.04:gh=0.01:bh=-0.03,cas=strength=0.45")
STYLE_GRADE = {
    "STL-CINEMA-HDR": CINEMA_GRADE_FILTER,
    "STL-DARK": "colorbalance=bs=0.06:rh=0.05,vibrance=intensity=0.25,unsharp=5:5:0.5",
    "STL-NEON": "vibrance=intensity=0.36,eq=contrast=1.10:saturation=1.22,cas=strength=0.50",
    "STL-CLEAN": "vibrance=intensity=0.22,eq=contrast=1.05:saturation=1.12,cas=strength=0.40",
    "STL-ROAST": "vibrance=intensity=0.32,eq=contrast=1.12:saturation=1.18,cas=strength=0.45",
}
STYLE_PACK_TOKENS = {
    "STL-CINEMA-HDR": {"accent": "#FFD13B", "secondary": "#00F5D4", "ass_accent": "&H003BD1FF&", "stroke": 5},
    "STL-DARK": {"accent": "#FFD13B", "secondary": "#06B6D4", "ass_accent": "&H003BD1FF&", "stroke": 5},
    "STL-NEON": {"accent": "#00F5D4", "secondary": "#F72585", "ass_accent": "&H00D4F500&", "stroke": 6},
    "STL-CLEAN": {"accent": "#38BDF8", "secondary": "#10B981", "ass_accent": "&H00F8BD38&", "stroke": 5},
    "STL-ROAST": {"accent": "#FFE600", "secondary": "#FF2A54", "ass_accent": "&H00542AFF&", "stroke": 7},
}
REQUIRED_FILTERS = ["ass", "loudnorm", "aformat", "apad", "areverse", "silenceremove", "sidechaincompress", "amix", "zoompan",
                    "overlay", "scale", "vibrance", "eq", "colorbalance", "cas", "unsharp", "noise", "blackdetect",
                    "freezedetect", "ebur128", "tile", "anoisesrc", "aevalsrc", "highpass", "lowshelf", "highshelf",
                    "equalizer", "acompressor", "deesser", "alimiter"]
# Encode profiles per tier (App G.3 + §7.5.5 table). Bitrate caps follow YouTube SDR guidance (VERIFIED-LIVE 2 Nov 2026).
ENCODE = {
    "1080p_fhd": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-maxrate", "12M", "-bufsize", "24M", "-profile:v", "high"],
    "1440p_qhd": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-maxrate", "24M", "-bufsize", "48M", "-profile:v", "high"],
    "4k_uhd": ["-c:v", "libx265", "-preset", "fast", "-crf", "18", "-tag:v", "hvc1"],
    "8k_uhd": ["-c:v", "libx265", "-preset", "fast", "-crf", "19", "-tag:v", "hvc1"],
}
# Hard timeouts = base + factor × seconds of output (App K, ESTIMATE/TARGET; RVS_TIMEOUT_SCALE multiplies all)
TIMEOUT_FACTOR = {"1080p_fhd": 6.0, "1440p_qhd": 10.0, "4k_uhd": 25.0, "8k_uhd": 90.0}


def tmo(base: float, seconds: float, tier: str = "1080p_fhd") -> float:
    return (base + TIMEOUT_FACTOR.get(tier, 6.0) * seconds) * float(os.environ.get("RVS_TIMEOUT_SCALE", "1"))


@dataclass(frozen=True)
class CanvasLayout:
    """Resolution-independent layout. Base geometry is defined at 1080 short edge and scaled (1.0x/1.333x/2.0x/4.0x)."""
    width: int
    height: int

    @property
    def is_landscape(self) -> bool:
        return self.width > self.height

    @property
    def scale_factor(self) -> float:
        return max(1.0, min(self.width, self.height) / 1080.0)

    def s(self, v: float) -> int:
        return int(round(v * self.scale_factor))

    @property
    def card_size(self) -> tuple[int, int]:
        return (self.s(1040), self.s(820)) if self.is_landscape else (self.s(920), self.s(1260))

    @property
    def card_pos(self) -> tuple[int, int]:
        return (self.s(72), self.s(130)) if self.is_landscape else (self.s(80), self.s(240))

    @property
    def info_stage(self) -> tuple[int, int, int, int]:
        """16:9 right info stage (x, y, w, h) = 720×460 at (1140,130): ends at y=590, leaving y 620–1040 for the host."""
        return (self.s(1140), self.s(130), self.s(720), self.s(460))

    @property
    def star_y(self) -> int:
        return self.s(820 if self.is_landscape else 1120)

    @property
    def caption_margins(self) -> tuple[int, int, int]:
        return (self.s(120), self.s(480), self.s(75)) if self.is_landscape else (self.s(64), self.s(64), self.s(430))

    @property
    def anime_host_box(self) -> tuple[int, int, int]:
        """(x, y, size). 16:9: 420 px at (1460, 620) → right column below the info stage, right of captions (MarginR 480).
        9:16: 300 px at (64, 1160) → inside the 64 px side safe margin and above the 420 px bottom band."""
        if self.is_landscape:
            return (self.width - self.s(460), self.height - self.s(460), self.s(420))
        return (self.s(64), self.height - self.s(760), self.s(300))


def font_for(text: str, latin: str, deva: str) -> str:
    return deva if re.search(r"[ऀ-ॿ]", text or "") else latin


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    kw = {"layout_engine": ImageFont.Layout.RAQM} if features.check("raqm") else {}
    return ImageFont.truetype(path, size, **kw)


def fit_text(draw: ImageDraw.ImageDraw, text: str, font_path: str, max_w: int, max_h: int, start: int, minimum: int):
    """Greedy word-wrap + shrink until the block fits (max_w × max_h). Returns (font, lines). Never overflows: last resort ellipsis."""
    size = start
    while size >= minimum:
        font = load_font(font_path, size)
        words, lines, cur = (text or "").split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        line_h = int(size * 1.25)
        if len(lines) * line_h <= max_h and all(draw.textlength(l, font=font) <= max_w for l in lines):
            return font, lines
        size -= 2
    font = load_font(font_path, minimum)
    txt = (text or "")
    while txt and draw.textlength(txt + "…", font=font) > max_w:
        txt = txt[:-1]
    return font, [txt + "…"]


def draw_block(draw, xy, text, latin, deva, max_w, max_h, start, minimum, fill):
    font, lines = fit_text(draw, text, font_for(text, latin, deva), max_w, max_h, start, minimum)
    x, y = xy
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += int(font.size * 1.25)
    return y


def escape_ass_text(raw: str) -> str:
    return str(raw).replace("\\", "\\\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")


def extract_dominant_palette(im: Image.Image) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Pillow median-cut quantize (python-pillow/Pillow, OSS-SKL-04) → pick the 2 most vibrant of 8 palette colours."""
    import colorsys
    q = im.convert("RGB").resize((64, 64), Image.Resampling.BILINEAR).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[:24]
    counts = {idx: c for c, idx in q.getcolors()}
    scored = []
    for i in range(8):
        r, g, b = pal[i * 3:i * 3 + 3]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s >= 0.22 and v >= 0.25:
            scored.append((counts.get(i, 0) * s * v, h))
    if not scored:
        return (0, 245, 212), (255, 209, 59)
    scored.sort(reverse=True)
    h1 = scored[0][1]
    h2 = scored[1][1] if len(scored) > 1 else (h1 + 0.42) % 1.0
    to_rgb = lambda h, s: tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, 0.96))
    return to_rgb(h1, 0.88), to_rgb(h2, 0.85)


def ensure_poster_exists(poster_path: str, work_dir: str, title: str = "REVIEW STUDIO") -> str:
    if poster_path and os.path.exists(poster_path):
        return poster_path
    warn("RVS_WARN_003", "S8-L", f"poster missing ({poster_path or 'none'}) — synthetic gradient poster")
    fallback = os.path.join(work_dir, "synthetic_poster.jpg")
    if not os.path.exists(fallback):
        im = Image.new("RGB", (1080, 1920), "#090D1A")
        glow = Image.new("RGB", (1080, 1920), "#090D1A")
        gd = ImageDraw.Draw(glow)
        gd.ellipse([-180, 120, 780, 1080], fill="#00B4D8")
        gd.ellipse([320, 620, 1260, 1620], fill="#F72585")
        gd.ellipse([180, 260, 900, 980], fill="#FFD13B")
        im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(140)), 0.65)
        im.save(fallback, quality=94)
    return fallback


def prepare_poster_layers(poster_path, work_dir, asset_id, focus_y_ratio, canvas_w, canvas_h):
    """Backdrop (1.45x colour, GaussianBlur(42), dual light leaks) + rounded RGBA foreground card for one asset."""
    lay = CanvasLayout(canvas_w, canvas_h)
    src = ensure_poster_exists(poster_path, work_dir)
    safe = f"{re.sub(r'[^A-Za-z0-9_-]', '_', asset_id)}_{canvas_w}x{canvas_h}"
    bg_path, fg_path = os.path.join(work_dir, f"bg_blurred_{safe}.jpg"), os.path.join(work_dir, f"fg_card_{safe}.png")
    if os.path.exists(bg_path) and os.path.exists(fg_path):
        return bg_path, fg_path
    try:
        with Image.open(src) as raw:
            im = raw.convert("RGB")
    except (OSError, ValueError) as e:
        raise RvsError("RVS_ERR_003", f"{src}: {e}") from e
    if min(im.size) < 600:
        warn("RVS_WARN_109", "S8-L", f"{asset_id} only {im.size[0]}x{im.size[1]} px — upscaled card")
    p1, p2 = extract_dominant_palette(im)
    bg = ImageOps.fit(im, (lay.width, lay.height), Image.Resampling.LANCZOS, centering=(0.5, focus_y_ratio))
    bg = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.45).filter(ImageFilter.GaussianBlur(lay.s(42)))).enhance(0.72)
    leaks = Image.new("RGB", bg.size, (0, 0, 0))
    ld = ImageDraw.Draw(leaks)
    r = int(min(bg.size) * 0.55)
    ld.ellipse([-r // 2, -r // 3, r, r], fill=p1)
    ld.ellipse([bg.width - r, bg.height - r, bg.width + r // 2, bg.height + r // 3], fill=p2)
    from PIL import ImageChops
    bg = ImageChops.screen(bg, ImageEnhance.Brightness(leaks.filter(ImageFilter.GaussianBlur(lay.s(95)))).enhance(0.42))
    bg.save(bg_path, quality=94)
    tw, th = lay.card_size
    fg = ImageOps.fit(im, (tw, th), Image.Resampling.LANCZOS, centering=(0.5, focus_y_ratio))
    fg = ImageEnhance.Contrast(ImageEnhance.Color(fg).enhance(1.18)).enhance(1.06).convert("RGBA")
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw - 1, th - 1], radius=lay.s(28), fill=255)
    fg.putalpha(mask)
    d = ImageDraw.Draw(fg)
    d.rounded_rectangle([1, 1, tw - 2, th - 2], radius=lay.s(28), outline=p1 + (245,), width=lay.s(4))
    fg.save(fg_path)
    return bg_path, fg_path


def render_data_card(scene: dict, endcard: dict, work_dir: str, latin: str, deva: str, canvas_w: int, canvas_h: int,
                     style: str = "STL-CINEMA-HDR") -> str:
    """Frosted glass card (chapter/stat/split/quote/chart/verdict). All text is fitted (wrap+shrink) — never overflows."""
    lay = CanvasLayout(canvas_w, canvas_h)
    sc = lay.s
    w, h = lay.card_size
    tok = STYLE_PACK_TOKENS.get(style, STYLE_PACK_TOKENS["STL-CINEMA-HDR"])
    acc, sec = tok["accent"], tok["secondary"]
    card = Image.new("RGBA", (w, h), (12, 18, 36, 215))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([sc(20), sc(20), w // 2, h // 2], fill=ImageColor.getrgb(sec) + (68,))
    gd.ellipse([w // 2, h // 2 - sc(40), w - sc(20), h - sc(20)], fill=ImageColor.getrgb(acc) + (54,))
    card = Image.alpha_composite(card, glow.filter(ImageFilter.GaussianBlur(sc(65))))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=sc(28), fill=255)
    card.putalpha(mask)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([1, 1, w - 2, h - 2], radius=sc(28), outline=sec, width=sc(3))
    pad, inner = sc(54), w - sc(108)
    mode, cd = scene["fallback_mode"], scene.get("card_data", {})
    if mode == "chapter_card":
        y = draw_block(d, (pad, sc(72)), scene.get("chapter_id", "CH-01"), latin, deva, inner, sc(60), sc(40), sc(24), sec)
        y = draw_block(d, (pad, y + sc(20)), cd.get("headline", scene.get("top_badge", "CHAPTER")), latin, deva, inner, sc(240), sc(62), sc(32), "#FFFFFF")
        draw_block(d, (pad, y + sc(16)), cd.get("sub_label", ""), latin, deva, inner, sc(120), sc(30), sc(20), acc)
    elif mode == "quote_card":
        y = draw_block(d, (pad, sc(60)), cd.get("headline", "PUBLIC PULSE QUOTE"), latin, deva, inner, sc(60), sc(40), sc(24), acc)
        d.rounded_rectangle([pad, y + sc(20), w - pad, h - sc(140)], radius=sc(20), fill=(255, 255, 255, 22), outline=acc, width=sc(2))
        draw_block(d, (pad + sc(26), y + sc(44)), cd.get("quote_text", ""), latin, deva, inner - sc(52), h - y - sc(220), sc(40), sc(22), "#FFFFFF")
        draw_block(d, (pad, h - sc(110)), "— " + cd.get("quote_source", "Source in fact_sheet.md"), latin, deva, inner, sc(60), sc(30), sc(20), sec)
    elif mode == "chart_card":
        y = draw_block(d, (pad, sc(52)), cd.get("headline", "SCORE CHART"), latin, deva, inner, sc(60), sc(40), sc(24), acc)
        bars = cd.get("chart_bars", [])[:6]
        row_h = max(sc(40), (h - y - sc(80)) // max(1, len(bars)))
        for i, b in enumerate(bars):
            by = y + sc(30) + i * row_h
            draw_block(d, (pad, by), b["label"], latin, deva, sc(300), row_h, sc(30), sc(18), "#F8FAFC")
            frac = max(0.02, min(1.0, b["value"] / b["max"]))
            x0, x1 = pad + sc(320), w - pad
            d.rounded_rectangle([x0, by + sc(6), x1, by + sc(34)], radius=sc(12), fill=(255, 255, 255, 30))
            d.rounded_rectangle([x0, by + sc(6), x0 + int((x1 - x0) * frac), by + sc(34)], radius=sc(12), fill=sec)
    elif mode in ("stat_card", "split_card"):
        y = draw_block(d, (pad, sc(52)), cd.get("headline", "KEY BREAKDOWN"), latin, deva, inner, sc(60), sc(40), sc(24), acc)
        y = draw_block(d, (pad, y + sc(8)), cd.get("big_stat", ""), latin, deva, inner, sc(90), sc(62), sc(30), "#FFFFFF")
        y = draw_block(d, (pad, y + sc(4)), cd.get("sub_label", ""), latin, deva, inner, sc(50), sc(30), sc(18), "#CBD5E1")
        col_w = (w - sc(140)) // 2
        for col, (title_k, items_k, colour, sign) in enumerate((("left_title", "left_items", sec, "+"), ("right_title", "right_items", "#FF2A54", "-"))):
            x = pad + col * (col_w + sc(32))
            draw_block(d, (x, y + sc(20)), cd.get(title_k, "PROS" if col == 0 else "CONS"), latin, deva, col_w, sc(50), sc(36), sc(20), colour)
            for i, item in enumerate(cd.get(items_k, [])[:4]):
                py = y + sc(80) + i * sc(74)
                d.rounded_rectangle([x, py, x + col_w, py + sc(58)], radius=sc(14), fill=(255, 255, 255, 24), outline=colour, width=sc(2))
                draw_block(d, (x + sc(18), py + sc(10)), f"{sign} {item}", latin, deva, col_w - sc(36), sc(44), sc(30), sc(16), "#F8FAFC")
    else:  # verdict_card
        y = draw_block(d, (pad, sc(52)), endcard.get("header_label", "INTERNET VERDICT"), latin, deva, inner, sc(60), sc(40), sc(24), acc)
        r_num, r_max = float(endcard.get("rating_numeric", 0)), float(endcard.get("rating_max", 5))
        y = draw_block(d, (pad, y + sc(8)), f"{r_num:g} / {r_max:g}", latin, deva, inner, sc(80), sc(62), sc(30), "#FFFFFF")
        d.rounded_rectangle([pad, y + sc(10), w - pad, y + sc(36)], radius=sc(12), fill=(255, 255, 255, 30))
        d.rounded_rectangle([pad, y + sc(10), pad + int(inner * max(0.05, min(1, r_num / r_max))), y + sc(36)], radius=sc(12), fill=sec)
        y = draw_block(d, (pad, y + sc(56)), endcard.get("verdict_stamp", ""), latin, deva, inner, sc(60), sc(40), sc(24), acc)
        for i, p in enumerate(endcard.get("pros", [])[:3] + endcard.get("cons", [])[:3]):
            sign, col = ("+", sec) if i < len(endcard.get("pros", [])[:3]) else ("-", "#FF2A54")
            draw_block(d, (pad, y + sc(14) + i * sc(56)), f"{sign} {p}", latin, deva, inner, sc(52), sc(30), sc(18), col)
    safe = f"{re.sub(r'[^A-Za-z0-9_-]', '_', scene['asset_id'])}_b{scene['beat']:03d}_{canvas_w}x{canvas_h}"
    out = os.path.join(work_dir, f"fg_card_{safe}.png")
    card.save(out)
    return out


def build_ass_vector_stars(start_ts, end_ts, rating_numeric, rating_max=5, y_pos=1120, canvas_w=1080, canvas_h=1920) -> str:
    """5 vector stars (\\an7 + \\pos + \\p1), clipped half-star, scaled; rating normalised to /5. Lines joined with REAL newlines."""
    r5 = max(0.0, min(5.0, float(rating_numeric) / float(rating_max) * 5.0))
    k = max(1.0, min(canvas_w, canvas_h) / 1080.0)
    fsc, step, half, sh = int(round(100 * k)), int(round(75 * k)), int(round(24 * k)), int(round(48 * k))
    x0 = int(round((canvas_w - 348.0 * k) / 2.0))
    tag = lambda x: f"\\an7\\fscx{fsc}\\fscy{fsc}\\pos({x},{y_pos})\\p1"
    lines = []
    for i in range(5):
        x, diff = x0 + i * step, r5 - i
        if diff >= 0.75:
            lines.append(f"Dialogue: 3,{start_ts},{end_ts},StarGold,,0,0,0,,{{{tag(x)}}}{STAR_VECTOR_PATH}{{\\p0}}")
        else:
            lines.append(f"Dialogue: 3,{start_ts},{end_ts},StarGray,,0,0,0,,{{{tag(x)}}}{STAR_VECTOR_PATH}{{\\p0}}")
            if diff >= 0.25:
                lines.append(f"Dialogue: 4,{start_ts},{end_ts},StarGold,,0,0,0,,{{\\clip({x},{y_pos},{x + half},{y_pos + sh}){tag(x)}}}{STAR_VECTOR_PATH}{{\\p0}}")
    return "\n".join(lines) + "\n"


def ms_to_ass_ts(ms: int) -> str:
    cs = int(round(max(0, ms) / 10.0))  # integer centiseconds: never prints '60.00' seconds
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def write_captions_ass(spec: dict, words: dict, work_dir: str, w: int, h: int) -> str:
    tok = STYLE_PACK_TOKENS.get(spec["meta"].get("style_pack", "STL-CINEMA-HDR"), STYLE_PACK_TOKENS["STL-CINEMA-HDR"])
    lay = CanvasLayout(w, h)
    ml, mr, mv = lay.caption_margins
    fs, bs = lay.s(48 if lay.is_landscape else 56), lay.s(32)
    st, sh = max(2, lay.s(tok["stroke"])), max(1, lay.s(2))
    top_mv = lay.s(60 if lay.is_landscape else 260)
    deva_caps = spec["meta"].get("caption_script") == "devanagari"
    font = "Noto Sans Devanagari" if deva_caps else "Poppins"
    header = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 1\nScaledBorderAndShadow: yes\n\n"
              "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
              f"Style: Default,{font},{fs},&H00FFFFFF,{tok['ass_accent']},&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{st},{sh},2,{ml},{mr},{mv},1\n"
              f"Style: TopBadge,Poppins,{bs},{tok['ass_accent']},&H00FFFFFF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,3,{lay.s(10)},0,7,{lay.s(72)},{lay.s(72)},{top_mv},1\n"
              "Style: StarGold,Poppins,48,&H003BD1FF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
              "Style: StarGray,Poppins,48,&H00555555,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n\n"
              "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = []
    chunks = words["chunks"]
    for c in chunks:
        txt = escape_ass_text(c["show"])
        hl = escape_ass_text(c.get("highlight_word", "").strip())
        if hl and hl in txt:
            txt = txt.replace(hl, f"{{\\1c{tok['ass_accent']}}}{hl}{{\\1c&H00FFFFFF&}}", 1)
        ev.append(f"Dialogue: 2,{ms_to_ass_ts(c['start_ms'])},{ms_to_ass_ts(c['end_ms'] + c['pause_after_ms'])},Default,,0,0,0,,{txt}")
    for b, (s_ms, e_ms) in beat_windows(spec, words).items():
        badge = next((s.get("top_badge") for s in spec["scenes"] if s["beat"] == b and s.get("top_badge")), None)
        if badge:
            ev.append(f"Dialogue: 1,{ms_to_ass_ts(s_ms)},{ms_to_ass_ts(e_ms)},TopBadge,,0,0,0,,{escape_ass_text(badge)}")
    ec = spec.get("endcard", {})
    if ec.get("enabled", True) and chunks:
        last = max(c["beat"] for c in chunks)
        vc = [c for c in chunks if c["beat"] == last]
        ev.append(build_ass_vector_stars(ms_to_ass_ts(vc[0]["start_ms"]), ms_to_ass_ts(vc[-1]["end_ms"] + vc[-1]["pause_after_ms"]),
                                         ec["rating_numeric"], ec["rating_max"], lay.star_y, w, h).rstrip("\n"))
    path = os.path.join(work_dir, "captions.ass")
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(ev) + "\n")
    return path


def beat_windows(spec: dict, words: dict) -> dict[int, tuple[int, int]]:
    """Scene beat → (start_ms, end_ms): from the first chunk of the beat to the first chunk of the next scene beat."""
    starts = {}
    for c in words["chunks"]:
        starts.setdefault(c["beat"], c["start_ms"])
    beats = sorted(b for b in {s["beat"] for s in spec["scenes"]} if b in starts)
    total = words["total_duration_ms"]
    return {b: (starts[b], starts[beats[i + 1]] if i + 1 < len(beats) else total) for i, b in enumerate(beats)}


SFX_RECIPES = {  # §7.6 recipes (stereo via aformat); durations whoosh 0.22, pop 0.09, riser 0.65, stamp 0.28 s
    "whoosh": "anoisesrc=d=0.22:c=pink:r=48000,afade=t=in:d=0.06,afade=t=out:st=0.12:d=0.10,lowpass=f=1800,highpass=f=220,volume=0.28",
    "pop": "sine=f=520:d=0.09:r=48000,afade=t=out:st=0.02:d=0.07,volume=0.32",
    "riser": "aevalsrc='0.22*sin(2*PI*(180+420*t)*t)':d=0.65:s=48000,afade=t=in:d=0.45,afade=t=out:st=0.55:d=0.10",
    "stamp": "aevalsrc='0.45*exp(-14*t)*sin(2*PI*78*t)+0.15*exp(-60*t)*sin(2*PI*950*t)':d=0.28:s=48000",
}


def synthesize_sfx_bed_wav(spec: dict, words: dict, work_dir: str) -> str:
    total = int(words["total_duration_ms"] * 48)
    bed = array("h", bytes(total * 4))
    starts = {b: s for b, (s, _) in beat_windows(spec, words).items()}
    cache = {}
    for sc in spec["scenes"]:
        kind = sc.get("sfx", "none")
        if kind == "none" or sc["beat"] not in starts:
            continue
        if kind not in cache:
            p = os.path.join(work_dir, f"sfx_{kind}.wav")
            run_cmd(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", SFX_RECIPES[kind], "-af",
                     "aformat=sample_rates=48000:channel_layouts=stereo:sample_fmts=s16", p], "S8-L", 30)
            with wave.open(p, "rb") as wf:
                cache[kind] = array("h", wf.readframes(wf.getnframes()))
        smp, off = cache[kind], starts[sc["beat"]] * 48 * 2
        for i, v in enumerate(smp):  # additive mix with clip guard
            j = off + i
            if j >= len(bed):
                break
            bed[j] = max(-32767, min(32767, bed[j] + v))
    path = os.path.join(work_dir, "sfx_bed.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes(bed.tobytes())
    return path


def _loudnorm_two_pass(src: str, dst: str, work_dir: str, dur: float) -> dict:
    p1 = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                  "-f", "null", "-"], "S8-L", tmo(30, dur), "RVS_ERR_050")
    blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr)
    if not blocks:
        raise RvsError("RVS_ERR_050", "loudnorm pass-1 JSON missing")
    st = json.loads(blocks[-1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:measured_LRA={st['input_lra']}:"
          f"measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true:print_format=json,"
          "aformat=sample_rates=48000:channel_layouts=stereo")
    p2 = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", src, "-af", af, "-ar", "48000", "-ac", "2", dst],
                 "S8-L", tmo(30, dur), "RVS_ERR_050")
    b2 = re.findall(r"\{[^{}]*\"normalization_type\"[^{}]*\}", p2.stderr)
    norm = json.loads(b2[-1]).get("normalization_type", "unknown") if b2 else "unknown"
    if norm.lower() != "linear":
        log_event("INFO", "S8-L", "loudnorm_mode", None, f"loudnorm used {norm} mode (linear not possible for this mix)")
    return {"pass1": st, "normalization_type": norm}


def mix_and_normalize_audio_two_pass(voice_wav, sfx_wav, work_dir, total_dur_s, bgm_wav=None, duck_db=-20.0) -> str:
    """Voice stem → RVS-VOICE-MASTER chain (fallback safe → bypass, RVS_WARN_053) → + SFX + sidechain-ducked BGM → two-pass loudnorm."""
    D = f"{total_dur_s:.3f}"
    raw = os.path.join(work_dir, "audio_raw_mix.wav")
    chains = [voice_master_chain(), VOICE_MASTER_CHAIN_SAFE, None]
    if chains[0] is None:
        chains = [None]
    for i, chain in enumerate(chains):
        vpre = f"aformat=sample_rates=48000:channel_layouts=stereo{(',' + chain) if chain else ''},apad=whole_dur={D}"
        if bgm_wav and os.path.exists(bgm_wav):
            vol = 10 ** ((duck_db + 13.0) / 20.0)  # bed level before ducking; −13 dB headroom so the ducked bed sits ≈ duck_db under voice
            fc = (f"[0:a]{vpre},asplit=2[vsc][vmix];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={D}[s];"
                  f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={vol:.3f},apad=whole_dur={D}[b];"
                  "[b][vsc]sidechaincompress=threshold=0.015:ratio=6:attack=15:release=280[bd];"
                  "[vmix][s][bd]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[out]")
            ins = ["-i", voice_wav, "-i", sfx_wav, "-i", bgm_wav]
        else:
            fc = (f"[0:a]{vpre}[v];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={D}[s];"
                  "[v][s]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]")
            ins = ["-i", voice_wav, "-i", sfx_wav]
        try:
            run_cmd(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[out]", "-t", D, "-ar", "48000", "-ac", "2", raw],
                    "S8-L", tmo(30, total_dur_s), "RVS_ERR_050", cwd=work_dir)
            break
        except RvsError as e:
            if i + 1 >= len(chains):
                raise
            warn("RVS_WARN_053", "S8-L", f"voice chain {'v1' if i == 0 else 'safe'} failed → {'safe' if i == 0 else 'bypass'} ({e.detail[:80]})")
    out = os.path.join(work_dir, "audio_master_48k.wav")
    _loudnorm_two_pass(raw, out, work_dir, total_dur_s)
    return out


def _valid_segment(path: str, expect_s: float, fps: int) -> bool:
    if not os.path.exists(path) or os.path.getsize(path) < 4096:
        return False
    try:
        return abs(ffprobe_duration(path) - expect_s) <= 1.5 / fps
    except RvsError:
        return False


def render_scene(scene, bg, fg, dur_s, work_dir, w, h, fps, tier) -> str:
    """One scene → scene_{beat:03d}.mp4 (video only). Ken Burns via 2x-supersampled zoompan on a SINGLE still (anti-jitter).
    Cards get a minimum 1.00→1.03 drift so freezedetect never sees a static card (§6.4 #5)."""
    lay = CanvasLayout(w, h)
    out = os.path.join(work_dir, f"scene_{scene['beat']:03d}.mp4")
    if _valid_segment(out, dur_s, fps):
        warn("RVS_WARN_124", "S8-L", f"scene {scene['beat']} reused from cache")
        return out
    if os.path.exists(out):
        warn("RVS_WARN_052", "S8-L", f"scene {scene['beat']} cache invalid → re-render")
    cw, ch = lay.card_size
    cx, cy = lay.card_pos
    frames = max(1, int(round(dur_s * fps)))
    zmax = 1.06 if scene.get("fallback_mode") == "poster_zoom" else 1.03
    inc = (zmax - 1.0) / frames
    motion = scene.get("motion", "zoom_in")
    z = f"min(1+{inc:.6f}*on,{zmax})" if motion != "zoom_out" else f"max({zmax}-{inc:.6f}*on,1)"
    fy = float(scene.get("focus_y_ratio", 0.5))
    x = "iw/2-(iw/zoom/2)"
    y = f"ih*{fy}-(ih/zoom*{fy})"
    if motion == "pan_left":
        x = f"(iw-iw/zoom)*(1-on/{frames})"
    elif motion == "pan_right":
        x = f"(iw-iw/zoom)*on/{frames}"
    elif motion == "pan_up":
        y = f"(ih-ih/zoom)*(1-on/{frames})"
    elif motion == "pan_down":
        y = f"(ih-ih/zoom)*on/{frames}"
    fc = (f"[1:v]format=rgba,scale={cw * 2}:{ch * 2}:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={cw}x{ch}:fps={fps}[fg];"
          f"[0:v]scale={w}:{h},format=rgba[bg];[bg][fg]overlay={cx}:{cy}:format=auto,format=yuv420p[v]")
    tmp = out + ".part.mp4"
    run_cmd(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(fps), "-t", f"{dur_s:.3f}", "-i", bg, "-i", fg,
             "-filter_complex", fc, "-map", "[v]", "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
             "-pix_fmt", "yuv420p", "-r", str(fps), tmp], "S8-L", tmo(30, dur_s, "1080p_fhd"), "RVS_ERR_050", cwd=work_dir)
    os.replace(tmp, out)
    return out


def render_all_scenes(spec, words, work_dir, latin, deva, w, h, fps) -> list[tuple[str, float]]:
    win = beat_windows(spec, words)
    out = []
    for sc in sorted(spec["scenes"], key=lambda s: s["beat"]):
        if sc["beat"] not in win:
            continue
        s_ms, e_ms = win[sc["beat"]]
        dur = max(0.5, (e_ms - s_ms) / 1000.0)
        if sc["fallback_mode"] == "poster_zoom" or sc["asset_id"].startswith(("AST-P", "AST-S")):
            bg, fg = prepare_poster_layers(sc.get("asset_file") and os.path.join(work_dir, sc["asset_file"]), work_dir,
                                           sc["asset_id"], sc.get("focus_y_ratio", 0.28), w, h)
        else:
            bg, _ = prepare_poster_layers("", work_dir, "AST-BG", 0.5, w, h)
            fg = render_data_card(sc, spec.get("endcard", {}), work_dir, latin, deva, w, h, spec["meta"].get("style_pack", "STL-CINEMA-HDR"))
        out.append((render_scene(sc, bg, fg, dur, work_dir, w, h, fps, spec["meta"].get("resolution_tier", "1080p_fhd")), dur))
    return out


def concat_scenes(segments, work_dir) -> str:
    lst = os.path.join(work_dir, "scenes.ffconcat")
    with open(lst, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n" + "".join(f"file '{os.path.basename(p)}'\n" for p, _ in segments))
    out = os.path.join(work_dir, "scenes_concat.mp4")
    run_cmd(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], "S8-L", 120, "RVS_ERR_055", cwd=work_dir)
    expect = sum(d for _, d in segments)
    if abs(ffprobe_duration(out) - expect) > 0.2:
        raise RvsError("RVS_ERR_055", f"concat {ffprobe_duration(out):.2f}s vs expected {expect:.2f}s")
    return out


def final_encode(video_in, audio_in, ass_file, out_mp4, work_dir, spec, char_concat=None) -> str:
    """Host overlay → style grade → captions (fontsdir) → optional UHD upscale (+cas/unsharp) → dither → BT.709 matrix → encode."""
    m = spec["meta"]
    tier, fps = m.get("resolution_tier", "1080p_fhd"), int(m["fps"])
    W, H = int(m["width"]), int(m["height"])
    work_w, work_h = (1920, 1080) if W > H else (1080, 1920)
    lay = CanvasLayout(work_w, work_h)
    hx, hy, hs = lay.anime_host_box
    grade = STYLE_GRADE.get(m.get("style_pack", "STL-CINEMA-HDR"), CINEMA_GRADE_FILTER)
    chain = [grade, f"ass=filename={os.path.basename(ass_file)}:fontsdir={FONTS_DIR}"]
    if (W, H) != (work_w, work_h):
        chain += [f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp", "cas=strength=0.55",
                  "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=0.65:chroma_msize_x=3:chroma_msize_y=3:chroma_amount=0.35"]
    pix = "yuv420p10le" if m.get("hdr_10bit") else "yuv420p"
    chain += ["noise=alls=2:allf=t+u", f"scale=out_color_matrix=bt709:out_range=tv,format={pix}"]
    if char_concat and os.path.exists(char_concat):
        fc = (f"[2:v]scale={hs}:{hs},format=rgba[host];[0:v][host]overlay={hx}:{hy}:eof_action=pass:format=auto,{','.join(chain)}[v]")
        extra = ["-f", "concat", "-safe", "0", "-i", char_concat]
    else:
        fc = f"[0:v]{','.join(chain)}[v]"
        extra = []
    enc = list(ENCODE.get(tier, ENCODE["1080p_fhd"]))
    if pix == "yuv420p10le" and enc[1] == "libx264":
        enc = list(ENCODE["4k_uhd"])
    dur = ffprobe_duration(video_in)
    tmp = out_mp4 + ".part.mp4"
    run_cmd(["ffmpeg", "-v", "error", "-y", "-i", video_in, "-i", audio_in, *extra, "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
             *enc, "-pix_fmt", pix, "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
             "-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", tmp],
            "S8-L", tmo(60, dur, tier), "RVS_ERR_050", cwd=work_dir)
    os.replace(tmp, out_mp4)
    return out_mp4


def build(spec_path, words_path, voice_wav, work_dir, out_mp4, latin, deva, char_concat=None) -> str:
    spec = json.load(open(spec_path, encoding="utf-8"))
    words = json.load(open(words_path, encoding="utf-8"))
    m = spec["meta"]
    W, H, fps = int(m["width"]), int(m["height"]), int(m["fps"])
    work_w, work_h = (1920, 1080) if W > H else (1080, 1920)
    check_disk_space(work_dir, {"1080p_fhd": 2048, "1440p_qhd": 4096, "4k_uhd": 8192, "8k_uhd": 20480}.get(m.get("resolution_tier", "1080p_fhd"), 2048))
    stage_start("S8-L", f"render {W}x{H}@{fps} tier={m.get('resolution_tier')}")
    ass = write_captions_ass(spec, words, work_dir, work_w, work_h)
    sfx = synthesize_sfx_bed_wav(spec, words, work_dir)
    bgm = spec.get("bgm", {})
    bgm_path = os.path.join(work_dir, bgm["bed_file"]) if bgm.get("enabled") and bgm.get("bed_file") else None
    audio = mix_and_normalize_audio_two_pass(voice_wav, sfx, work_dir, words["total_duration_ms"] / 1000.0, bgm_path, bgm.get("duck_db", -20))
    segs = render_all_scenes(spec, words, work_dir, latin, deva, work_w, work_h, fps)
    video = concat_scenes(segs, work_dir)
    final_encode(video, audio, ass, out_mp4, work_dir, spec, char_concat)
    stage_end("S8-L", f"→ {out_mp4}")
    return out_mp4


def main():
    ap = argparse.ArgumentParser(description="S8-L/S12 renderer")
    for k in ("spec", "words", "voice", "work", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--char-timeline", default=None)
    ap.add_argument("--latin-font", default=str(FONTS_DIR / "Poppins-Bold.ttf"))
    ap.add_argument("--deva-font", default=str(FONTS_DIR / "NotoSansDevanagari-Bold.ttf"))
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    build(a.spec, a.words, a.voice, a.work, a.out, a.latin_font, a.deva_font, a.char_timeline)


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S8-L"))
