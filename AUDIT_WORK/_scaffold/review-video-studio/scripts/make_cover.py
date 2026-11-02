"""make_cover.py — S10-L/S13 covers: 9:16 cover (all text inside 1080×1350 box, y∈[285,1635], x∈[84,996]), 3:4 grid preview,
two 16:9 YouTube thumbnails (v1 = title-led, v2 = verdict-led) (File 19, PRD v5.1 App G.4, OSS-SKL-04).
CLI: python scripts/make_cover.py --poster poster.jpg --title "..." --rating "3.5/5" --stamp "ONE-TIME WATCH" --work WORK
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageEnhance, ImageOps  # noqa: E402

from build_video import FONTS_DIR, draw_block, ensure_poster_exists  # noqa: E402
from rvs_common import RvsError, log_event, main_wrapper  # noqa: E402

SAFE = (84, 285, 996, 1635)  # 4:5 feed box inside the 3:4 profile-grid crop (y 240–1680)


def generate_covers(poster_path: str, title: str, rating_str: str, stamp: str, work_dir: str, latin: str, deva: str) -> dict:
    src = ensure_poster_exists(poster_path, work_dir, title)
    try:
        with Image.open(src) as raw:
            im = raw.convert("RGB")
    except (OSError, ValueError) as e:
        raise RvsError("RVS_ERR_003", f"{src}: {e}") from e
    cov = ImageEnhance.Brightness(ImageOps.fit(im, (1080, 1920), Image.Resampling.LANCZOS, centering=(0.5, 0.28))).enhance(0.75)
    d = ImageDraw.Draw(cov)
    d.rounded_rectangle([84, 320, 640, 410], radius=20, fill="#FFD13B")
    draw_block(d, (110, 334), stamp.upper(), latin, deva, 510, 64, 42, 22, "#0B0D13")
    d.rounded_rectangle([84, 1300, 996, 1600], radius=24, fill="#0B0D13", outline="#FFD13B", width=4)
    y = draw_block(d, (116, 1328), title.upper(), latin, deva, 848, 160, 68, 30, "#FFFFFF")
    draw_block(d, (116, max(y + 8, 1500)), f"VERDICT: {rating_str}", latin, deva, 848, 70, 56, 28, "#00F5D4")
    out = {"cover_9x16": os.path.join(work_dir, "cover_9x16.png"), "cover_grid_3x4_preview": os.path.join(work_dir, "cover_grid_3x4_preview.png")}
    cov.save(out["cover_9x16"])
    cov.crop((0, 240, 1080, 1680)).save(out["cover_grid_3x4_preview"])
    for v, (main_txt, sub_txt) in {"v1": (title.upper(), rating_str), "v2": (f"VERDICT {rating_str}", stamp.upper())}.items():
        th = ImageOps.fit(im, (1280, 720), Image.Resampling.LANCZOS, centering=(0.5, 0.28))
        td = ImageDraw.Draw(th)
        td.rounded_rectangle([40, 430, 900, 680], radius=20, fill="#0B0D13", outline="#FFD13B", width=4)  # left: YouTube duration badge sits bottom-right
        yy = draw_block(td, (66, 452), main_txt, latin, deva, 808, 130, 64, 30, "#FFD13B")
        draw_block(td, (66, max(yy + 6, 600)), sub_txt, latin, deva, 808, 60, 44, 24, "#FFFFFF")
        out[f"thumb_16x9_{v}"] = os.path.join(work_dir, f"thumb_16x9_{v}.png")
        th.save(out[f"thumb_16x9_{v}"])
    return out


def main():
    ap = argparse.ArgumentParser(description="covers + thumbnails")
    ap.add_argument("--poster", default="")
    for k in ("title", "rating", "stamp", "work"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--latin-font", default=str(FONTS_DIR / "Poppins-Bold.ttf"))
    ap.add_argument("--deva-font", default=str(FONTS_DIR / "NotoSansDevanagari-Bold.ttf"))
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    res = generate_covers(a.poster, a.title, a.rating, a.stamp, a.work, a.latin_font, a.deva_font)
    log_event("INFO", "S10-L", "covers_done", None, ", ".join(os.path.basename(p) for p in res.values()))
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S10-L"))
