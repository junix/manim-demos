from pathlib import Path

from manim_demos import SCENES


def test_every_scene_has_primary_and_motion_artifacts() -> None:
    assert len(SCENES) >= 12
    for slug in SCENES:
        assert (Path("out") / f"{slug}-transparent.png").exists()
        assert (Path("out") / f"{slug}.mp4").stat().st_size > 10_000
