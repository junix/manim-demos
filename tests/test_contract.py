import inspect
import json
import re
from pathlib import Path

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
