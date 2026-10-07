from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

from manim_demos import SCENES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "manim_demos" / "scenes.py"
MEDIA = ROOT / "media"
OUT = ROOT / "out"


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, cwd=ROOT)


def newest(pattern: str, since: float | None = None) -> Path:
    # With `since`, artifacts left by earlier runs are ignored, so a render
    # that silently produced nothing never picks up a stale media match.
    matches = [
        path
        for path in MEDIA.rglob(pattern)
        if since is None or path.stat().st_mtime >= since
    ]
    if not matches:
        raise RuntimeError(f"Manim did not produce {pattern}")
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def validate_png(path: Path) -> dict[str, object]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A").histogram()
    pixels = image.width * image.height
    transparent = alpha[0]
    visible = pixels - sum(alpha[:16])
    colors = image.getcolors(maxcolors=pixels) or []
    colorful = sum(count for count, rgba in colors if rgba[3] > 16 and max(rgba[:3]) - min(rgba[:3]) > 24)
    if transparent < pixels * 0.08 or visible < pixels * 0.025 or colorful < 1600:
        raise RuntimeError(f"{path.name}: weak RGBA content t={transparent} v={visible} c={colorful}")
    return {
        "size": image.size,
        "transparent_pct": round(100 * transparent / pixels, 1),
        "visible_pct": round(100 * visible / pixels, 1),
        "colorful": colorful,
    }


def probe_duration(video: Path) -> float:
    probe = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(video),
        ],
        text=True,
    ).strip()
    try:
        duration = float(probe)
    except ValueError:
        raise RuntimeError(f"{video.name}: invalid video duration {probe!r}") from None
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError(f"{video.name}: invalid video duration {probe!r}")
    return duration


def main() -> None:
    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe is required")
    OUT.mkdir(exist_ok=True)
    report = []
    for slug, class_name in SCENES.items():
        started = time.time()
        run(
            [
                "manim",
                "-ql",
                "-s",
                "-t",
                "--disable_caching",
                "--progress_bar",
                "none",
                "--media_dir",
                str(MEDIA),
                "--output_file",
                slug,
                str(SOURCE),
                class_name,
            ]
        )
        still_source = newest(f"{slug}*.png", started)
        started = time.time()
        run(
            [
                "manim",
                "-ql",
                "--disable_caching",
                "--progress_bar",
                "none",
                "--media_dir",
                str(MEDIA),
                "--output_file",
                slug,
                str(SOURCE),
                class_name,
            ]
        )
        video_source = newest(f"{slug}.mp4", started)
        # Stage both artifacts from this render run and validate them before
        # either touches out/: a failed movie render, a weak still, or an
        # undecodable video must leave the previously delivered pair in place.
        with tempfile.TemporaryDirectory() as staging:
            staged_still = Path(staging) / f"{slug}-transparent.png"
            staged_video = Path(staging) / f"{slug}.mp4"
            shutil.copy2(still_source, staged_still)
            shutil.copy2(video_source, staged_video)
            duration = probe_duration(staged_video)
            item = {
                "scene": slug,
                **validate_png(staged_still),
                "video_seconds": round(duration, 2),
            }
            shutil.copy2(staged_still, OUT / staged_still.name)
            shutil.copy2(staged_video, OUT / staged_video.name)
        print(json.dumps(item))
        report.append(item)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
