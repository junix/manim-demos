import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from manim import Scene
from PIL import Image

from manim_demos import SCENES, scenes

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MP4_FTYP = b"ftyp"
# Acceptance floors mirrored from scripts/render.py validate_png().
PNG_TRANSPARENT_FRACTION = 0.08
PNG_VISIBLE_FRACTION = 0.025
PNG_COLORFUL_MIN = 1600
CATALOG_FIELDS = {"id", "use", "question", "family", "complexity", "tags"}

# scripts/render.py lives outside the package; load it by path to test its helpers directly.
RENDER_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render.py"


def _load_render_module():
    spec = importlib.util.spec_from_file_location("manim_demos_render_script", RENDER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render = _load_render_module()

# Synthetic frames sized so every acceptance floor lands on an integer pixel count.
FRAME_SIZE = (100, 100)
FRAME_PIXELS = FRAME_SIZE[0] * FRAME_SIZE[1]
CLEAR_PIXEL = (0, 0, 0, 0)
HIDDEN_PIXEL = (18, 24, 30, 15)
FLAT_ALPHA_PIXEL = (128, 128, 128, 16)
OPAQUE_GRAY_PIXEL = (128, 128, 128, 255)
CHROMATIC_PIXEL = (200, 40, 60, 255)
CHROMA_AT_ALPHA_FLOOR_PIXEL = (200, 40, 60, 16)
SPREAD_AT_FLOOR_PIXEL = (152, 128, 128, 255)


def write_frame(path: Path, segments: list[tuple[int, tuple[int, int, int, int]]]) -> Path:
    pixels = [color for count, color in segments for _ in range(count)]
    assert len(pixels) == FRAME_PIXELS, segments
    image = Image.new("RGBA", FRAME_SIZE)
    image.putdata(pixels)
    image.save(path, format="PNG")
    return path


def test_scenes_registry_resolves_every_slug_to_a_defined_scene() -> None:
    assert len(SCENES) >= 12
    for slug, class_name in SCENES.items():
        assert SLUG.fullmatch(slug), slug
        scene_class = getattr(scenes, class_name)
        assert inspect.isclass(scene_class) and issubclass(scene_class, Scene), class_name
    defined_here = {
        name
        for name, obj in vars(scenes).items()
        if inspect.isclass(obj) and issubclass(obj, Scene) and obj.__module__ == scenes.__name__
    }
    assert defined_here == set(SCENES.values())
    assert len(set(SCENES.values())) == len(SCENES)


def test_catalog_lists_every_scene_exactly_once() -> None:
    entries = json.loads(Path("catalog.json").read_text())
    for entry in entries:
        assert set(entry) == CATALOG_FIELDS, entry["id"]
        for field in ("id", "use", "question", "family", "complexity"):
            value = entry[field]
            assert isinstance(value, str) and value.strip(), (entry["id"], field)
        tags = entry["tags"]
        assert isinstance(tags, list) and tags, entry["id"]
        assert all(isinstance(tag, str) and tag.strip() for tag in tags), entry["id"]
    ids = [entry["id"] for entry in entries]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(SCENES)


def test_every_scene_has_primary_and_motion_artifacts() -> None:
    for slug in SCENES:
        png = Path("out") / f"{slug}-transparent.png"
        mp4 = Path("out") / f"{slug}.mp4"
        assert png.exists()
        assert png.read_bytes()[:8] == PNG_MAGIC
        with Image.open(png) as image:
            rgba = image.convert("RGBA")
            assert rgba.size == (854, 480)
            alpha = rgba.getchannel("A").histogram()
            pixels = rgba.width * rgba.height
            visible = pixels - sum(alpha[:16])
            colorful = sum(
                count
                for count, rgba_value in rgba.getcolors(maxcolors=pixels) or []
                if rgba_value[3] > 16 and max(rgba_value[:3]) - min(rgba_value[:3]) > 24
            )
        assert alpha[0] >= pixels * PNG_TRANSPARENT_FRACTION
        assert visible >= pixels * PNG_VISIBLE_FRACTION
        assert colorful >= PNG_COLORFUL_MIN
        assert mp4.stat().st_size > 10_000
        assert mp4.read_bytes()[4:8] == MP4_FTYP


def test_validate_png_accepts_a_frame_exactly_at_the_acceptance_floors(tmp_path) -> None:
    path = write_frame(
        tmp_path / "boundary.png",
        [
            (800, CLEAR_PIXEL),  # exactly the 8% transparency floor
            (150, HIDDEN_PIXEL),  # alpha 15: below the visibility cutoff
            (1600, CHROMATIC_PIXEL),  # exactly the colorful floor
            (7450, FLAT_ALPHA_PIXEL),  # alpha 16: visible but never colorful
        ],
    )
    assert render.validate_png(path) == {
        "size": FRAME_SIZE,
        "transparent_pct": 8.0,
        "visible_pct": 90.5,
        "colorful": 1600,
    }


@pytest.mark.parametrize(
    ("filename", "segments", "detail"),
    [
        ("opaque.png", [(FRAME_PIXELS, OPAQUE_GRAY_PIXEL)], "t=0 v=10000 c=0"),
        (
            "low-transparency.png",
            [(799, CLEAR_PIXEL), (150, HIDDEN_PIXEL), (1600, CHROMATIC_PIXEL), (7451, FLAT_ALPHA_PIXEL)],
            "t=799 v=9051 c=1600",
        ),
        (
            "nearly-invisible.png",
            [(800, CLEAR_PIXEL), (9150, HIDDEN_PIXEL), (50, CHROMATIC_PIXEL)],
            "t=800 v=50 c=50",
        ),
        (
            "low-colorful.png",
            [(800, CLEAR_PIXEL), (150, HIDDEN_PIXEL), (1599, CHROMATIC_PIXEL), (7451, FLAT_ALPHA_PIXEL)],
            "t=800 v=9050 c=1599",
        ),
        (
            "chroma-at-alpha-floor.png",
            [(800, CLEAR_PIXEL), (1600, CHROMA_AT_ALPHA_FLOOR_PIXEL), (7600, FLAT_ALPHA_PIXEL)],
            "t=800 v=9200 c=0",
        ),
        (
            "spread-at-floor.png",
            [(800, CLEAR_PIXEL), (1600, SPREAD_AT_FLOOR_PIXEL), (7600, FLAT_ALPHA_PIXEL)],
            "t=800 v=9200 c=0",
        ),
    ],
)
def test_validate_png_rejects_frames_below_the_floors(tmp_path, filename, segments, detail) -> None:
    path = write_frame(tmp_path / filename, segments)
    with pytest.raises(RuntimeError) as excinfo:
        render.validate_png(path)
    assert str(excinfo.value) == f"{filename}: weak RGBA content {detail}"


def test_newest_raises_when_media_has_no_match(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(render, "MEDIA", tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        render.newest("scene*.png")
    assert str(excinfo.value) == "Manim did not produce scene*.png"


def test_newest_returns_the_most_recent_match_recursively(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(render, "MEDIA", tmp_path)
    stale = tmp_path / "videos" / "scene-stale.png"
    stale.parent.mkdir()
    fresh = tmp_path / "scene-fresh.png"
    stale.write_bytes(PNG_MAGIC)
    fresh.write_bytes(PNG_MAGIC)
    os.utime(stale, (1_000_000_000, 1_000_000_000))
    os.utime(fresh, (1_600_000_000, 1_600_000_000))
    assert render.newest("scene*.png") == fresh


def test_run_prefixes_and_executes_from_the_repo_root(capfd) -> None:
    command = [sys.executable, "-c", "import os; print(os.getcwd())"]
    render.run(command)
    lines = capfd.readouterr().out.splitlines()
    assert lines[0] == "+ " + " ".join(command)
    assert lines[1] == str(render.ROOT)


def test_run_propagates_a_nonzero_exit(capsys) -> None:
    command = [sys.executable, "-c", "raise SystemExit(3)"]
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        render.run(command)
    assert excinfo.value.returncode == 3
    assert capsys.readouterr().out == "+ " + " ".join(command) + "\n"
