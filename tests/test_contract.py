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
# Acceptance floors mirrored from tools/render.py validate_png().
PNG_TRANSPARENT_FRACTION = 0.08
PNG_VISIBLE_FRACTION = 0.025
PNG_COLORFUL_MIN = 1600
CATALOG_FIELDS = {"id", "use", "question", "family", "complexity", "tags"}

# tools/render.py lives outside the package; load it by path to test its helpers directly.
RENDER_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "render.py"


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


def test_validate_png_rounds_reported_percentages_to_one_decimal(tmp_path) -> None:
    path = write_frame(
        tmp_path / "rounding.png",
        [
            (833, CLEAR_PIXEL),  # 8.33% transparent: the reported value must round, not truncate
            (150, HIDDEN_PIXEL),
            (1600, CHROMATIC_PIXEL),
            (7417, FLAT_ALPHA_PIXEL),
        ],
    )
    assert render.validate_png(path) == {
        "size": FRAME_SIZE,
        "transparent_pct": 8.3,
        "visible_pct": 90.2,
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


def test_newest_returns_a_lone_match_from_any_depth(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(render, "MEDIA", tmp_path)
    lone = tmp_path / "videos" / "1080p60" / "only.png"  # no siblings to pick between
    lone.parent.mkdir(parents=True)
    lone.write_bytes(PNG_MAGIC)
    assert render.newest("only.png") == lone


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


def test_main_requires_ffprobe_before_any_rendering(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    monkeypatch.setattr(render, "OUT", tmp_path / "out")
    commands: list[list[str]] = []
    monkeypatch.setattr(render, "run", lambda command: commands.append(command))
    with pytest.raises(SystemExit) as excinfo:
        render.main()
    assert str(excinfo.value) == "ffprobe is required"
    assert commands == []  # the guard fires before a single manim invocation
    assert not (tmp_path / "out").exists()  # ...and before the output tree is created


def test_main_renders_every_scene_and_prints_the_report(monkeypatch, tmp_path, capsys) -> None:
    out = tmp_path / "out"
    media = tmp_path / "media"
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    events: list[tuple] = []

    def fake_run(command: list[str]) -> None:
        events.append(("run", command))

    def fake_newest(pattern: str) -> Path:
        events.append(("newest", pattern))
        return media / pattern.replace("*", "-found")

    def fake_copy2(source: Path, target: Path) -> None:
        events.append(("copy", source, target))

    def fake_check_output(command: list[str], text: bool) -> str:
        assert text is True
        events.append(("probe", command))
        return "3.249\n"  # rounds to 3.25 via round(float(probe), 2)

    def fake_validate_png(path: Path) -> dict[str, object]:
        events.append(("validate", path))
        return {"size": (854, 480), "transparent_pct": 8.4, "visible_pct": 91.2, "colorful": 23456}

    monkeypatch.setattr(render, "run", fake_run)
    monkeypatch.setattr(render, "newest", fake_newest)
    monkeypatch.setattr(render, "validate_png", fake_validate_png)
    monkeypatch.setattr(render.shutil, "copy2", fake_copy2)
    monkeypatch.setattr(render.subprocess, "check_output", fake_check_output)

    render.main()

    assert out.is_dir()  # OUT.mkdir(exist_ok=True) created the fresh output tree
    report = []
    expected_events = []
    for slug, class_name in SCENES.items():
        png = out / f"{slug}-transparent.png"
        video = out / f"{slug}.mp4"
        still = [
            "manim",
            "-ql",
            "-s",
            "-t",
            "--disable_caching",
            "--progress_bar",
            "none",
            "--media_dir",
            str(render.MEDIA),
            "--output_file",
            slug,
            str(render.SOURCE),
            class_name,
        ]
        movie = [
            "manim",
            "-ql",
            "--disable_caching",
            "--progress_bar",
            "none",
            "--media_dir",
            str(render.MEDIA),
            "--output_file",
            slug,
            str(render.SOURCE),
            class_name,
        ]
        probe = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(video),
        ]
        expected_events += [
            ("run", still),
            ("newest", f"{slug}*.png"),
            ("copy", media / f"{slug}-found.png", png),
            ("run", movie),
            ("newest", f"{slug}.mp4"),
            ("copy", media / f"{slug}.mp4", video),
            ("probe", probe),
            ("validate", png),
        ]
        report.append(
            {
                "scene": slug,
                "size": (854, 480),
                "transparent_pct": 8.4,
                "visible_pct": 91.2,
                "colorful": 23456,
                "video_seconds": 3.25,
            }
        )
    assert events == expected_events  # exact commands, copies, probes, and per-scene ordering
    lines = capsys.readouterr().out.splitlines()
    assert lines[: len(SCENES)] == [json.dumps(item) for item in report]
    assert "\n".join(lines[len(SCENES) :]) == json.dumps(report, indent=2)


def test_main_re_renders_into_an_existing_out_tree_without_clobbering(monkeypatch, tmp_path, capsys) -> None:
    out = tmp_path / "out"
    out.mkdir()  # a previous build already delivered artifacts; exist_ok must tolerate them
    stale = out / "retired-scene-transparent.png"
    stale.write_bytes(PNG_MAGIC)
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)
    monkeypatch.setattr(render, "newest", lambda pattern: tmp_path / "media" / pattern.replace("*", "-found"))
    monkeypatch.setattr(render.shutil, "copy2", lambda source, target: None)
    monkeypatch.setattr(render.subprocess, "check_output", lambda command, text: "3.249\n")
    monkeypatch.setattr(
        render,
        "validate_png",
        lambda path: {"size": (854, 480), "transparent_pct": 8.4, "visible_pct": 91.2, "colorful": 23456},
    )

    render.main()

    assert stale.read_bytes() == PNG_MAGIC  # prior deliverables survive a re-render
    assert len(commands) == 2 * len(SCENES)  # every scene still gets its still + movie pass
    lines = capsys.readouterr().out.splitlines()
    assert [json.loads(line)["scene"] for line in lines[: len(SCENES)]] == list(SCENES)
    assert json.loads("\n".join(lines[len(SCENES) :]))[-1]["scene"] == list(SCENES)[-1]


def test_main_with_no_scenes_renders_nothing_and_prints_an_empty_report(
    monkeypatch, tmp_path, capsys
) -> None:
    out = tmp_path / "out"
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render, "SCENES", {})
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    copies: list[tuple[Path, Path]] = []
    probes: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)
    monkeypatch.setattr(
        render, "newest", lambda pattern: pytest.fail(f"newest({pattern!r}) called with no scenes")
    )
    monkeypatch.setattr(
        render.shutil, "copy2", lambda source, target: copies.append((source, target))
    )
    monkeypatch.setattr(
        render.subprocess, "check_output", lambda command, text: probes.append(command)
    )
    monkeypatch.setattr(
        render,
        "validate_png",
        lambda path: pytest.fail(f"validate_png({path!r}) called with no scenes"),
    )

    render.main()

    assert commands == []  # zero scenes means zero manim invocations...
    assert copies == []  # ...no artifact deliveries...
    assert probes == []  # ...and no duration probes
    assert out.is_dir()  # the output tree is still created before the loop
    assert list(out.iterdir()) == []
    assert capsys.readouterr().out == "[]\n"  # the final report degenerates to an empty list


def test_main_aborts_without_a_report_when_the_delivered_still_fails_validation(
    monkeypatch, tmp_path, capsys
) -> None:
    out = tmp_path / "out"
    media = tmp_path / "media"
    media.mkdir()
    still_source = media / "still.png"
    still_source.write_bytes(PNG_MAGIC)  # real bytes: the real copy2 must deliver them unchanged
    movie_source = media / "movie.mp4"
    movie_source.write_bytes(MP4_FTYP)
    first_slug, first_class = next(iter(SCENES.items()))
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    probes: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)

    def newest_both_artifacts(pattern: str) -> Path:
        return movie_source if pattern == f"{first_slug}.mp4" else still_source

    monkeypatch.setattr(render, "newest", newest_both_artifacts)

    def fake_check_output(command: list[str], text: bool) -> str:
        probes.append(command)
        return "3.249\n"

    monkeypatch.setattr(render.subprocess, "check_output", fake_check_output)

    def reject(path: Path) -> dict[str, object]:
        raise RuntimeError(f"{path.name}: weak RGBA content t=0 v=10000 c=0")

    monkeypatch.setattr(render, "validate_png", reject)

    with pytest.raises(RuntimeError) as excinfo:
        render.main()

    assert str(excinfo.value) == f"{first_slug}-transparent.png: weak RGBA content t=0 v=10000 c=0"
    assert len(commands) == 2  # both the still pass and the movie pass ran before validation
    assert commands[0][-2:] == [str(render.SOURCE), first_class]
    assert "-s" in commands[0]  # the first is the transparent still render...
    assert commands[1][-2:] == [str(render.SOURCE), first_class]
    assert "-s" not in commands[1]  # ...the second the movie render
    assert probes == [
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(out / f"{first_slug}.mp4"),  # the probe targets the delivered copy, not the media source
        ]
    ]
    delivered = sorted(out.iterdir())
    assert delivered == sorted([out / f"{first_slug}-transparent.png", out / f"{first_slug}.mp4"])
    assert (out / f"{first_slug}-transparent.png").read_bytes() == PNG_MAGIC
    assert (out / f"{first_slug}.mp4").read_bytes() == MP4_FTYP  # no rollback of delivered artifacts
    assert capsys.readouterr().out == ""  # the per-scene line follows validation, so nothing is printed


def test_main_aborts_without_a_report_when_manim_output_goes_missing(
    monkeypatch, tmp_path, capsys
) -> None:
    out = tmp_path / "out"
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)

    def missing_newest(pattern: str) -> Path:
        raise RuntimeError(f"Manim did not produce {pattern}")

    monkeypatch.setattr(render, "newest", missing_newest)
    first_slug = next(iter(SCENES))
    with pytest.raises(RuntimeError) as excinfo:
        render.main()
    assert str(excinfo.value) == f"Manim did not produce {first_slug}*.png"
    assert len(commands) == 1  # only the first scene's still render ran before the abort
    assert commands[0][-2:] == [str(render.SOURCE), next(iter(SCENES.values()))]
    assert capsys.readouterr().out == ""  # no per-scene line and no final report on the error path
    assert list(out.iterdir()) == []  # and nothing partial landed in the output tree


def test_main_keeps_completed_scenes_report_lines_when_a_later_scene_aborts(
    monkeypatch, tmp_path, capsys
) -> None:
    out = tmp_path / "out"
    media = tmp_path / "media"
    media.mkdir()
    still_source = media / "still.png"
    still_source.write_bytes(PNG_MAGIC)  # real bytes: the real copy2 must deliver them unchanged
    movie_source = media / "movie.mp4"
    movie_source.write_bytes(MP4_FTYP)
    first_slug, first_class = next(iter(SCENES.items()))
    second_slug, second_class = list(SCENES.items())[1]
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    probes: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)

    def newest_until_the_second_scene(pattern: str) -> Path:
        if pattern == f"{second_slug}*.png":
            raise RuntimeError(f"Manim did not produce {pattern}")
        return movie_source if pattern == f"{first_slug}.mp4" else still_source

    monkeypatch.setattr(render, "newest", newest_until_the_second_scene)

    def fake_check_output(command: list[str], text: bool) -> str:
        probes.append(command)
        return "3.249\n"

    monkeypatch.setattr(render.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(
        render,
        "validate_png",
        lambda path: {"size": (854, 480), "transparent_pct": 8.4, "visible_pct": 91.2, "colorful": 23456},
    )

    with pytest.raises(RuntimeError) as excinfo:
        render.main()

    assert str(excinfo.value) == f"Manim did not produce {second_slug}*.png"
    assert len(commands) == 3  # the first scene's still + movie passes, then the second scene's still pass
    assert [command[-1] for command in commands] == [first_class, first_class, second_class]
    assert "-s" in commands[0] and "-s" not in commands[1] and "-s" in commands[2]
    assert probes == [
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(out / f"{first_slug}.mp4"),  # only the first scene's delivered video is ever probed
        ]
    ]
    delivered = sorted(out.iterdir())
    assert delivered == sorted([out / f"{first_slug}-transparent.png", out / f"{first_slug}.mp4"])
    assert (out / f"{first_slug}-transparent.png").read_bytes() == PNG_MAGIC
    assert (out / f"{first_slug}.mp4").read_bytes() == MP4_FTYP  # scene 1's deliveries survive the abort
    assert capsys.readouterr().out == (
        json.dumps(
            {
                "scene": first_slug,
                "size": (854, 480),
                "transparent_pct": 8.4,
                "visible_pct": 91.2,
                "colorful": 23456,
                "video_seconds": 3.25,
            }
        )
        + "\n"
    )  # the per-scene line is printed inside the loop, so completed scenes stay reported; no final report


def test_main_refuses_to_render_when_out_is_occupied_by_a_regular_file(monkeypatch, tmp_path) -> None:
    out = tmp_path / "out"
    out.write_text("occupied")  # exist_ok tolerates an existing directory, never a stray file
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)
    with pytest.raises(FileExistsError) as excinfo:
        render.main()
    assert str(excinfo.value) == f"[Errno 17] File exists: '{out}'"
    assert excinfo.value.filename == str(out)
    assert commands == []  # the failure fires before a single manim invocation
    assert out.read_text() == "occupied"  # and the occupying file is left untouched


def test_main_aborts_mid_scene_when_the_movie_artifact_goes_missing(
    monkeypatch, tmp_path, capsys
) -> None:
    out = tmp_path / "out"
    media = tmp_path / "media"
    media.mkdir()
    still_source = media / "still.png"
    still_source.write_bytes(PNG_MAGIC)  # real bytes: the real copy2 must deliver them unchanged
    first_slug, first_class = next(iter(SCENES.items()))
    monkeypatch.setattr(render, "OUT", out)
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffprobe")
    commands: list[list[str]] = []
    probes: list[list[str]] = []
    monkeypatch.setattr(render, "run", commands.append)

    def newest_until_the_movie(pattern: str) -> Path:
        if pattern == f"{first_slug}.mp4":
            raise RuntimeError(f"Manim did not produce {pattern}")
        return still_source

    monkeypatch.setattr(render, "newest", newest_until_the_movie)
    monkeypatch.setattr(
        render.subprocess, "check_output", lambda command, text: probes.append(command)
    )

    with pytest.raises(RuntimeError) as excinfo:
        render.main()

    assert str(excinfo.value) == f"Manim did not produce {first_slug}.mp4"
    assert len(commands) == 2  # both the still pass and the movie pass ran before the abort
    assert commands[0][-2:] == [str(render.SOURCE), first_class]
    assert "-s" in commands[0]  # the first is the transparent still render...
    assert commands[1][-2:] == [str(render.SOURCE), first_class]
    assert "-s" not in commands[1]  # ...the second the movie render
    assert probes == []  # a duration is never probed for an undelivered video
    assert list(out.iterdir()) == [out / f"{first_slug}-transparent.png"]  # delivered still stays: no rollback
    assert (out / f"{first_slug}-transparent.png").read_bytes() == PNG_MAGIC
    assert capsys.readouterr().out == ""  # no per-scene line and no final report on the error path
