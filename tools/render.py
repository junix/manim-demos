from __future__ import annotations

import json
import shutil
import subprocess
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


def newest(pattern: str) -> Path:
    matches = list(MEDIA.rglob(pattern))
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


def main() -> None:
    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe is required")
    OUT.mkdir(exist_ok=True)
    report = []
    for slug, class_name in SCENES.items():
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
        png = OUT / f"{slug}-transparent.png"
        shutil.copy2(newest(f"{slug}*.png"), png)
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
        video = OUT / f"{slug}.mp4"
        shutil.copy2(newest(f"{slug}.mp4"), video)
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
        item = {"scene": slug, **validate_png(png), "video_seconds": round(float(probe), 2)}
        print(json.dumps(item))
        report.append(item)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
