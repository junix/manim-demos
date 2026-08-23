from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    PI,
    RIGHT,
    UP,
    Arrow,
    Axes,
    Circle,
    Create,
    Dot,
    FadeIn,
    LaggedStart,
    Line,
    Polygon,
    Rectangle,
    RoundedRectangle,
    Scene,
    Square,
    Text,
    VGroup,
)

INK = "#e8f5fb"
MUTED = "#7f9fb4"
CYAN = "#54d6c6"
AMBER = "#ffd166"
ROSE = "#ff6f91"
INDIGO = "#7b9cff"
VIOLET = "#b889ff"


def title_block(title: str, subtitle: str) -> VGroup:
    title_text = Text(title, font="Avenir Next", weight="BOLD", font_size=37, color=INK)
    subtitle_text = Text(subtitle, font="Avenir Next", font_size=17, color=MUTED)
    title_text.to_corner(UP + LEFT, buff=0.55)
    subtitle_text.next_to(title_text, DOWN, aligned_edge=LEFT, buff=0.13)
    rule = Line(
        subtitle_text.get_left() + DOWN * 0.18,
        subtitle_text.get_left() + RIGHT * 3.7 + DOWN * 0.18,
        color="#4e7187",
        stroke_width=1.4,
    )
    return VGroup(title_text, subtitle_text, rule)


class AlgorithmTrace(Scene):
    def construct(self) -> None:
        header = title_block("BINARY SEARCH / TRACE 06", "INTERVAL HALVING AS A VISUAL INVARIANT")
        values = [3, 8, 12, 19, 24, 31, 42, 47, 58, 63, 71, 86, 91]
        cards = VGroup()
        for index, value in enumerate(values):
            box = RoundedRectangle(
                width=0.78,
                height=0.72,
                corner_radius=0.1,
                stroke_color="#6689a0",
                stroke_width=1.5,
                fill_color="#132740",
                fill_opacity=0.78,
            )
            number = Text(str(value), font="Avenir Next", font_size=22, color=INK)
            card = VGroup(box, number)
            card.move_to(LEFT * 5.2 + RIGHT * index * 0.86 + UP * 0.35)
            cards.add(card)
        target = VGroup(
            Circle(radius=0.37, color=ROSE, stroke_width=3.2),
            Text("42", font="Avenir Next", font_size=20, color=ROSE),
        ).arrange()
        target_label = Text("TARGET", font="Avenir Next", font_size=13, color=MUTED).next_to(
            target, UP, buff=0.15
        )
        target_group = VGroup(target_label, target).move_to(RIGHT * 4.7 + UP * 2.05)
        tracks = VGroup()
        intervals = [(0, 12, 6, "mid = 6"), (0, 5, 2, "mid = 2"), (3, 5, 4, "mid = 4"), (5, 5, 5, "found")]
        for row, (lo, hi, mid, note) in enumerate(intervals):
            y = -0.75 - row * 0.85
            start = cards[lo].get_center()[0]
            end = cards[hi].get_center()[0]
            line = Line(
                [start, y, 0],
                [end, y, 0],
                color=[CYAN, INDIGO, AMBER, ROSE][row],
                stroke_width=6 - row * 0.65,
            )
            left_tick = Line([start, y - 0.13, 0], [start, y + 0.13, 0], color=line.get_color())
            right_tick = Line([end, y - 0.13, 0], [end, y + 0.13, 0], color=line.get_color())
            dot = Dot([cards[mid].get_center()[0], y, 0], radius=0.09, color=AMBER if row < 3 else ROSE)
            note_text = Text(note, font="Avenir Next", font_size=15, color=INK).next_to(
                right_tick, RIGHT, buff=0.18
            )
            tracks.add(VGroup(line, left_tick, right_tick, dot, note_text))
        caption = Text(
            "Each comparison preserves:  target ∈ [low, high]", font="Avenir Next", font_size=18, color=CYAN
        ).to_edge(DOWN, buff=0.42)
        self.play(
            FadeIn(header),
            LaggedStart(*(FadeIn(card, shift=UP * 0.12) for card in cards), lag_ratio=0.045),
            run_time=1.2,
        )
        self.play(FadeIn(target_group, shift=LEFT * 0.2))
        self.play(LaggedStart(*(Create(track) for track in tracks), lag_ratio=0.22), run_time=2.0)
        cards[6][0].set_stroke(ROSE, width=3).set_fill("#4b263e", opacity=0.92)
        self.play(FadeIn(caption))
        self.wait(0.5)


class FourierPhasors(Scene):
    def construct(self) -> None:
        header = title_block("FOURIER PHASORS", "ROTATING VECTORS SYNTHESIZE A WAVE")
        center = LEFT * 3.5 + DOWN * 0.15
        radii = [1.55, 0.72, 0.43, 0.3]
        frequencies = [1, 3, 5, 7]
        colors = [CYAN, INDIGO, ROSE, AMBER]
        chains = VGroup()
        point = center.copy()
        time = 0.73
        for radius, frequency, color in zip(radii, frequencies, colors, strict=True):
            circle = Circle(radius=radius, color=color, stroke_width=1.7, stroke_opacity=0.55).move_to(point)
            angle = frequency * time
            end = point + radius * np.array([np.cos(angle), np.sin(angle), 0])
            arrow = Arrow(
                point, end, buff=0, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.12
            )
            chains.add(circle, arrow, Dot(end, radius=0.055, color=color))
            point = end
        axes = Axes(
            x_range=[0, 6, 1],
            y_range=[-2.3, 2.3, 1],
            x_length=5.5,
            y_length=4.4,
            axis_config={"color": "#57768d", "stroke_opacity": 0.7, "include_ticks": False},
        ).move_to(RIGHT * 3.35 + DOWN * 0.15)
        wave = axes.plot(
            lambda x: (
                1.55 * np.sin(x + time)
                + 0.72 * np.sin(3 * (x + time))
                + 0.43 * np.sin(5 * (x + time))
                + 0.3 * np.sin(7 * (x + time))
            ),
            x_range=[0, 6, 0.025],
            color=ROSE,
            stroke_width=3,
        )
        bridge = Line(
            point,
            axes.c2p(
                0,
                1.55 * np.sin(time)
                + 0.72 * np.sin(3 * time)
                + 0.43 * np.sin(5 * time)
                + 0.3 * np.sin(7 * time),
            ),
            color="#b9cfdd",
            stroke_width=1.2,
            stroke_opacity=0.6,
        )
        legend = (
            VGroup(
                *[
                    VGroup(
                        Dot(color=c), Text(f"n = {f}", font="Avenir Next", font_size=15, color=INK)
                    ).arrange(RIGHT, buff=0.13)
                    for f, c in zip(frequencies, colors, strict=True)
                ]
            )
            .arrange(RIGHT, buff=0.48)
            .to_edge(DOWN, buff=0.42)
        )
        self.play(
            FadeIn(header), LaggedStart(*(Create(item) for item in chains), lag_ratio=0.08), run_time=1.5
        )
        self.play(Create(axes), Create(bridge), Create(wave), run_time=1.6)
        self.play(FadeIn(legend))
        self.wait(0.5)


class GeometricProof(Scene):
    def construct(self) -> None:
        header = title_block("PYTHAGORAS / REARRANGEMENT", "THE SAME FOUR TRIANGLES, TWO INTERIORS")
        colors = [CYAN, INDIGO, ROSE, AMBER]
        panels = VGroup()
        for panel_x, mode in ((-3.45, "c²"), (3.45, "a² + b²")):
            frame = Square(
                side_length=4.35, color="#6c8aa0", stroke_width=1.8, fill_color="#11263d", fill_opacity=0.42
            ).move_to([panel_x, -0.35, 0])
            tris = VGroup()
            base = np.array([[-2.05, -2.05, 0], [0.55, -2.05, 0], [-2.05, -0.45, 0]])
            for i in range(4):
                tri = Polygon(*base, color=colors[i], stroke_width=2, fill_color=colors[i], fill_opacity=0.27)
                tri.rotate(i * PI / 2, about_point=ORIGIN).shift([panel_x, -0.35, 0])
                tris.add(tri)
            if mode == "c²":
                inner = (
                    Square(
                        side_length=1.72,
                        color=VIOLET,
                        stroke_width=2.6,
                        fill_color="#4a2c64",
                        fill_opacity=0.42,
                    )
                    .rotate(0.56)
                    .move_to([panel_x, -0.35, 0])
                )
                label = Text("c²", font="Avenir Next", weight="BOLD", font_size=31, color=VIOLET).move_to(
                    inner
                )
            else:
                inner_a = Rectangle(
                    width=1.55,
                    height=1.55,
                    color=CYAN,
                    stroke_width=2.5,
                    fill_color="#19413e",
                    fill_opacity=0.55,
                ).move_to([panel_x - 0.82, -0.35, 0])
                inner_b = Rectangle(
                    width=1.08,
                    height=1.08,
                    color=AMBER,
                    stroke_width=2.5,
                    fill_color="#493d1d",
                    fill_opacity=0.55,
                ).move_to([panel_x + 0.75, -0.35, 0])
                inner = VGroup(inner_a, inner_b)
                label = VGroup(
                    Text("a²", font="Avenir Next", font_size=26, color=CYAN).move_to(inner_a),
                    Text("b²", font="Avenir Next", font_size=24, color=AMBER).move_to(inner_b),
                )
            panels.add(VGroup(frame, tris, inner, label))
        equality = Text(
            "SAME OUTER AREA  −  SAME TRIANGLES", font="Avenir Next", font_size=17, color=MUTED
        ).to_edge(DOWN, buff=0.58)
        therefore = Text(
            "c²  =  a² + b²", font="Avenir Next", weight="BOLD", font_size=28, color=INK
        ).next_to(equality, UP, buff=0.18)
        self.play(FadeIn(header), Create(panels[0][0]), Create(panels[1][0]))
        self.play(
            LaggedStart(*(FadeIn(panel[1], shift=UP * 0.1) for panel in panels), lag_ratio=0.25), run_time=1.5
        )
        self.play(FadeIn(panels[0][2:]), FadeIn(panels[1][2:]))
        self.play(FadeIn(therefore), FadeIn(equality))
        self.wait(0.5)


class GradientDescent(Scene):
    def construct(self) -> None:
        header = title_block("GRADIENT DESCENT", "LOSS LANDSCAPE / STEP SIZE / CONVERGENCE TRACE")
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[0, 8, 2],
            x_length=9.2,
            y_length=4.8,
            axis_config={"color": "#57768d", "include_ticks": False},
        ).shift(DOWN * 0.45)
        curve = axes.plot(
            lambda x: 0.28 * (x - 0.65) ** 2 + 0.22 * np.sin(3 * x) + 0.6,
            x_range=[-4, 4, 0.035],
            color=INDIGO,
            stroke_width=3,
        )
        xs = [-3.4, -2.25, -1.25, -0.35, 0.25, 0.58, 0.66]
        points = [axes.c2p(x, 0.28 * (x - 0.65) ** 2 + 0.22 * np.sin(3 * x) + 0.6) for x in xs]
        trace = VGroup(
            *[
                Arrow(
                    points[i],
                    points[i + 1],
                    buff=0.09,
                    color=[CYAN, INDIGO, VIOLET, ROSE, AMBER, CYAN][i],
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.18,
                )
                for i in range(len(points) - 1)
            ]
        )
        dots = VGroup(
            *[
                Dot(point, radius=0.085, color=AMBER if i < len(points) - 1 else ROSE)
                for i, point in enumerate(points)
            ]
        )
        notes = VGroup(
            *[
                Text(f"η{i + 1}", font="Avenir Next", font_size=13, color=MUTED).next_to(dot, UP, buff=0.08)
                for i, dot in enumerate(dots)
            ]
        )
        caption = Text(
            "adaptive steps settle inside the low-curvature basin",
            font="Avenir Next",
            font_size=17,
            color=CYAN,
        ).to_edge(DOWN, buff=0.38)
        self.play(FadeIn(header), Create(axes), Create(curve), run_time=1.1)
        self.play(
            LaggedStart(*(Create(arrow) for arrow in trace), lag_ratio=0.13),
            LaggedStart(*(FadeIn(dot) for dot in dots), lag_ratio=0.11),
            run_time=1.5,
        )
        self.play(FadeIn(notes), FadeIn(caption))
        self.wait(0.35)


class NeuralForwardPass(Scene):
    def construct(self) -> None:
        header = title_block("NEURAL FORWARD PASS", "FEATURE FLOW / BOTTLENECK / CLASS ACTIVATION")
        sizes = [6, 8, 5, 7, 3]
        xs = np.linspace(-5.0, 5.0, len(sizes))
        layers = VGroup()
        connections = VGroup()
        previous: list[Dot] = []
        for layer_index, (x, size) in enumerate(zip(xs, sizes, strict=True)):
            nodes = [
                Dot(
                    [x, (i - (size - 1) / 2) * 0.58 - 0.25, 0],
                    radius=0.09,
                    color=[CYAN, INDIGO, VIOLET, ROSE, AMBER][layer_index],
                )
                for i in range(size)
            ]
            if previous:
                for left in previous:
                    for right in nodes:
                        if int((left.get_y() + right.get_y()) * 10 + layer_index) % 3 == 0:
                            connections.add(
                                Line(
                                    left.get_center(),
                                    right.get_center(),
                                    color="#66869b",
                                    stroke_width=0.7,
                                    stroke_opacity=0.26,
                                )
                            )
            layer = VGroup(*nodes)
            label = Text(
                ["INPUT", "STEM", "LATENT", "ATTENTION", "CLASS"][layer_index],
                font="Avenir Next",
                font_size=13,
                color=MUTED,
            ).next_to(layer, DOWN, buff=0.22)
            layers.add(VGroup(layer, label))
            previous = nodes
        skip = Arrow(
            layers[1].get_top() + UP * 0.1,
            layers[3].get_top() + UP * 0.1,
            path_arc=-0.45,
            color=ROSE,
            buff=0.12,
            stroke_width=2.4,
        )
        self.play(FadeIn(header), Create(connections), run_time=1.0)
        self.play(
            LaggedStart(*(FadeIn(layer, shift=RIGHT * 0.15) for layer in layers), lag_ratio=0.14),
            run_time=1.4,
        )
        self.play(Create(skip))
        self.wait(0.35)


class SortingNetwork(Scene):
    def construct(self) -> None:
        header = title_block("BITONIC SORTING NETWORK", "PARALLEL COMPARE–SWAP STAGES / 8 INPUTS")
        ys = np.linspace(2.0, -2.7, 8)
        wires = VGroup(*[Line([-5.5, y, 0], [5.4, y, 0], color="#66869b", stroke_width=1.2) for y in ys])
        stages = [
            (0, 1, -4.5),
            (2, 3, -4.5),
            (4, 5, -4.5),
            (6, 7, -4.5),
            (0, 2, -3.2),
            (1, 3, -3.2),
            (4, 6, -3.2),
            (5, 7, -3.2),
            (1, 2, -1.9),
            (5, 6, -1.9),
            (0, 4, -0.5),
            (1, 5, -0.5),
            (2, 6, -0.5),
            (3, 7, -0.5),
            (0, 2, 0.9),
            (1, 3, 0.9),
            (4, 6, 0.9),
            (5, 7, 0.9),
            (0, 1, 2.3),
            (2, 3, 2.3),
            (4, 5, 2.3),
            (6, 7, 2.3),
            (1, 2, 3.7),
            (3, 4, 3.7),
            (5, 6, 3.7),
        ]
        comparators = VGroup()
        for a, b, x in stages:
            color = [CYAN, INDIGO, VIOLET, ROSE, AMBER][int((x + 5) * 2) % 5]
            comparators.add(
                VGroup(
                    Line([x, ys[a], 0], [x, ys[b], 0], color=color, stroke_width=2),
                    Dot([x, ys[a], 0], radius=0.07, color=color),
                    Dot([x, ys[b], 0], radius=0.07, color=color),
                )
            )
        labels = VGroup(
            *[
                Text(str(v), font="Avenir Next", font_size=15, color=INK).move_to([-5.85, y, 0])
                for v, y in zip([42, 7, 91, 18, 63, 5, 32, 27], ys, strict=True)
            ]
        )
        output = VGroup(
            *[
                Text(str(v), font="Avenir Next", font_size=15, color=CYAN).move_to([5.75, y, 0])
                for v, y in zip(sorted([42, 7, 91, 18, 63, 5, 32, 27]), ys, strict=True)
            ]
        )
        self.play(FadeIn(header), Create(wires), FadeIn(labels))
        self.play(LaggedStart(*(Create(stage) for stage in comparators), lag_ratio=0.035), run_time=2.0)
        self.play(FadeIn(output))
        self.wait(0.35)


class ProtocolStateMachine(Scene):
    def construct(self) -> None:
        header = title_block(
            "RESILIENT SESSION PROTOCOL", "LEGAL TRANSITIONS / RETRY BUDGET / TERMINAL STATES"
        )
        positions = {
            "IDLE": (-4.5, 0.8),
            "AUTH": (-2.2, 1.4),
            "ACTIVE": (0.3, 1.1),
            "DRAIN": (2.7, 1.6),
            "CLOSED": (4.7, 0.5),
            "RETRY": (-1.2, -2.0),
            "FAILED": (2.0, -2.1),
        }
        nodes = {}
        group = VGroup()
        for index, (name, (x, y)) in enumerate(positions.items()):
            ring = Circle(
                radius=0.55 if name not in {"ACTIVE", "FAILED"} else 0.68,
                color=[CYAN, INDIGO, VIOLET, ROSE, AMBER][index % 5],
                stroke_width=2.4,
                fill_color="#132740",
                fill_opacity=0.76,
            ).move_to([x, y, 0])
            label = Text(name, font="Avenir Next", font_size=15, color=INK).move_to(ring)
            nodes[name] = VGroup(ring, label)
            group.add(nodes[name])
        edges = [
            ("IDLE", "AUTH"),
            ("AUTH", "ACTIVE"),
            ("ACTIVE", "DRAIN"),
            ("DRAIN", "CLOSED"),
            ("AUTH", "RETRY"),
            ("ACTIVE", "RETRY"),
            ("RETRY", "AUTH"),
            ("RETRY", "FAILED"),
        ]
        arrows = VGroup(
            *[
                Arrow(
                    nodes[a].get_center(),
                    nodes[b].get_center(),
                    buff=0.62,
                    color=ROSE if b == "FAILED" else "#7896ab",
                    stroke_width=2,
                    max_tip_length_to_length_ratio=0.12,
                )
                for a, b in edges
            ]
        )
        budget = VGroup(
            *[
                Rectangle(width=0.42, height=0.12, color=AMBER, fill_color=AMBER, fill_opacity=0.75).shift(
                    LEFT * 1.65 + RIGHT * i * 0.52 + DOWN * 3.05
                )
                for i in range(5)
            ]
        )
        budget_label = Text("RETRY BUDGET", font="Avenir Next", font_size=12, color=MUTED).next_to(
            budget, LEFT, buff=0.2
        )
        self.play(FadeIn(header), LaggedStart(*(FadeIn(node) for node in group), lag_ratio=0.08))
        self.play(LaggedStart(*(Create(arrow) for arrow in arrows), lag_ratio=0.09), run_time=1.7)
        self.play(FadeIn(budget), FadeIn(budget_label))
        self.wait(0.35)


class BayesianUpdate(Scene):
    def construct(self) -> None:
        header = title_block("BAYESIAN UPDATE", "PRIOR × LIKELIHOOD → POSTERIOR")
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[0, 1.2, 0.2],
            x_length=10.1,
            y_length=4.5,
            axis_config={"color": "#57768d", "include_ticks": False},
        ).shift(DOWN * 0.45)
        prior = axes.plot(
            lambda x: np.exp(-0.5 * ((x + 1.1) / 1.35) ** 2) * 0.62,
            x_range=[-4, 4, 0.03],
            color=INDIGO,
            stroke_width=3,
        )
        likelihood = axes.plot(
            lambda x: np.exp(-0.5 * ((x - 1.0) / 0.7) ** 2) * 0.95,
            x_range=[-4, 4, 0.03],
            color=AMBER,
            stroke_width=3,
        )
        posterior = axes.plot(
            lambda x: np.exp(-0.5 * ((x - 0.48) / 0.57) ** 2) * 1.08,
            x_range=[-4, 4, 0.03],
            color=ROSE,
            stroke_width=4,
        )
        legend = (
            VGroup(
                *[
                    VGroup(
                        Line(ORIGIN, RIGHT * 0.45, color=color, stroke_width=4),
                        Text(name, font="Avenir Next", font_size=14, color=INK),
                    ).arrange(RIGHT, buff=0.12)
                    for name, color in (("prior", INDIGO), ("likelihood", AMBER), ("posterior", ROSE))
                ]
            )
            .arrange(RIGHT, buff=0.5)
            .to_edge(DOWN, buff=0.35)
        )
        evidence = VGroup(
            Line(axes.c2p(1.0, 0), axes.c2p(1.0, 1.05), color=CYAN, stroke_width=1.5),
            Text("evidence", font="Avenir Next", font_size=13, color=CYAN).move_to(axes.c2p(1.0, 1.12)),
        )
        self.play(FadeIn(header), Create(axes))
        self.play(Create(prior), Create(likelihood), Create(evidence), run_time=1.2)
        self.play(Create(posterior), FadeIn(legend), run_time=1.0)
        self.wait(0.35)


class OrbitalTransfer(Scene):
    def construct(self) -> None:
        header = title_block("ORBITAL TRANSFER", "TWO-BURN MANEUVER / PHASE ALIGNMENT / ENERGY CHANGE")
        center = LEFT * 0.8 + DOWN * 0.5
        inner = Circle(radius=1.35, color=CYAN, stroke_width=1.6, stroke_opacity=0.58).move_to(center)
        outer = Circle(radius=3.45, color=INDIGO, stroke_width=1.6, stroke_opacity=0.58).move_to(center)
        sun = Circle(radius=0.42, color=AMBER, fill_color=AMBER, fill_opacity=0.62).move_to(center)
        transfer = (
            Circle(radius=2.4, color=ROSE, stroke_width=3).stretch(1.45, 0).move_to(center + LEFT * 1.05)
        )
        craft_a = Dot(center + RIGHT * 1.35, radius=0.11, color=CYAN)
        craft_b = Dot(center + LEFT * 3.45, radius=0.13, color=INDIGO)
        burn_a = Arrow(
            craft_a.get_center(), craft_a.get_center() + UP * 0.85, buff=0.04, color=CYAN, stroke_width=3
        )
        burn_b = Arrow(
            craft_b.get_center(), craft_b.get_center() + DOWN * 0.95, buff=0.04, color=INDIGO, stroke_width=3
        )
        panel = (
            VGroup(
                Text("Δv₁   2.44 km/s", font="Avenir Next", font_size=16, color=CYAN),
                Text("coast   258 days", font="Avenir Next", font_size=16, color=MUTED),
                Text("Δv₂   1.47 km/s", font="Avenir Next", font_size=16, color=INDIGO),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.22)
            .to_edge(RIGHT, buff=0.55)
        )
        self.play(FadeIn(header), Create(inner), Create(outer), FadeIn(sun))
        self.play(Create(transfer), FadeIn(craft_a), FadeIn(craft_b), run_time=1.2)
        self.play(Create(burn_a), Create(burn_b), FadeIn(panel))
        self.wait(0.35)


class MatrixTransform(Scene):
    def construct(self) -> None:
        header = title_block("MATRIX TRANSFORM", "BASIS CHANGE / SHEAR / ROTATION")
        left_axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=4.7,
            y_length=4.7,
            axis_config={"color": "#57768d", "include_ticks": False},
        ).shift(LEFT * 3.2 + DOWN * 0.45)
        right_axes = left_axes.copy().shift(RIGHT * 6.4)
        source = Polygon(
            left_axes.c2p(-1, -1),
            left_axes.c2p(1.4, -1),
            left_axes.c2p(1.4, 1.2),
            left_axes.c2p(-1, 1.2),
            color=CYAN,
            fill_color=CYAN,
            fill_opacity=0.22,
            stroke_width=2.5,
        )
        matrix = np.array([[1.15, 0.72], [0.45, 1.3]])
        original = np.array([[-1, -1], [1.4, -1], [1.4, 1.2], [-1, 1.2]])
        transformed = original @ matrix.T
        target = Polygon(
            *(right_axes.c2p(x, y) for x, y in transformed),
            color=ROSE,
            fill_color=ROSE,
            fill_opacity=0.25,
            stroke_width=2.5,
        )
        arrow = Arrow(LEFT * 0.6 + DOWN * 0.45, RIGHT * 0.6 + DOWN * 0.45, color=AMBER, stroke_width=3)
        formula = Text(
            "A = [ 1.15  0.72 ; 0.45  1.30 ]", font="Avenir Next", font_size=17, color=INK
        ).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(header), Create(left_axes), Create(right_axes))
        self.play(FadeIn(source), Create(arrow), run_time=0.9)
        self.play(FadeIn(target), FadeIn(formula), run_time=0.9)
        self.wait(0.35)


class QueueingFlow(Scene):
    def construct(self) -> None:
        header = title_block("QUEUEING FLOW", "ARRIVAL RATE / SERVICE CAPACITY / BACKPRESSURE")
        blocks = VGroup()
        labels = [
            ("ARRIVALS", CYAN),
            ("GATEWAY", INDIGO),
            ("QUEUE", AMBER),
            ("WORKERS", VIOLET),
            ("RESULTS", ROSE),
        ]
        for i, (name, color) in enumerate(labels):
            box = RoundedRectangle(
                width=1.75,
                height=1.15,
                corner_radius=0.14,
                color=color,
                fill_color="#132740",
                fill_opacity=0.78,
                stroke_width=2,
            ).move_to(LEFT * 4.7 + RIGHT * i * 2.35 + UP * 0.4)
            label = Text(name, font="Avenir Next", font_size=14, color=INK).move_to(box)
            blocks.add(VGroup(box, label))
        arrows = VGroup(
            *[
                Arrow(
                    blocks[i].get_right(),
                    blocks[i + 1].get_left(),
                    buff=0.12,
                    color="#7896ab",
                    stroke_width=2.3,
                )
                for i in range(4)
            ]
        )
        queue = VGroup(
            *[
                Rectangle(
                    width=0.34, height=0.5 + 0.12 * (i % 4), color=AMBER, fill_color=AMBER, fill_opacity=0.62
                ).move_to(blocks[2].get_bottom() + DOWN * 0.72 + LEFT * 0.82 + RIGHT * i * 0.46)
                for i in range(5)
            ]
        )
        workers = VGroup(
            *[
                Circle(radius=0.18, color=VIOLET, fill_color=VIOLET, fill_opacity=0.45).move_to(
                    blocks[3].get_bottom()
                    + DOWN * 0.72
                    + LEFT * 0.48
                    + RIGHT * (i % 3) * 0.48
                    + DOWN * (i // 3) * 0.48
                )
                for i in range(6)
            ]
        )
        metrics = (
            VGroup(
                *[
                    Text(item, font="Avenir Next", font_size=15, color=color)
                    for item, color in (
                        ("λ = 840/s", CYAN),
                        ("μ = 960/s", VIOLET),
                        ("p99 = 84 ms", ROSE),
                        ("ρ = 0.875", AMBER),
                    )
                ]
            )
            .arrange(RIGHT, buff=0.62)
            .to_edge(DOWN, buff=0.38)
        )
        self.play(FadeIn(header), LaggedStart(*(FadeIn(block) for block in blocks), lag_ratio=0.1))
        self.play(LaggedStart(*(Create(arrow) for arrow in arrows), lag_ratio=0.12), run_time=1.2)
        self.play(FadeIn(queue), FadeIn(workers), FadeIn(metrics))
        self.wait(0.35)


class LSystemGrowth(Scene):
    def construct(self) -> None:
        header = title_block("L-SYSTEM GROWTH", "RECURSIVE BRANCHING / DEPTH 7 / PHYLLOTAXIS")
        branches = VGroup()

        def grow(start: np.ndarray, angle: float, length: float, depth: int) -> None:
            if depth == 0:
                branches.add(Dot(start, radius=0.045, color=ROSE))
                return
            end = start + np.array([np.cos(angle), np.sin(angle), 0]) * length
            branches.add(
                Line(
                    start,
                    end,
                    color=[CYAN, INDIGO, VIOLET, ROSE, AMBER][depth % 5],
                    stroke_width=0.7 + depth * 0.42,
                    stroke_opacity=0.82,
                )
            )
            grow(end, angle + 0.39 + 0.025 * depth, length * 0.74, depth - 1)
            grow(end, angle - 0.53 + 0.018 * depth, length * 0.70, depth - 1)

        grow(np.array([0.0, -3.25, 0.0]), PI / 2, 1.55, 7)
        generation = (
            VGroup(
                *[
                    Text(
                        f"G{i}",
                        font="Avenir Next",
                        font_size=12,
                        color=[CYAN, INDIGO, VIOLET, ROSE, AMBER][i % 5],
                    )
                    for i in range(1, 8)
                ]
            )
            .arrange(RIGHT, buff=0.42)
            .to_edge(DOWN, buff=0.3)
        )
        self.play(FadeIn(header))
        self.play(LaggedStart(*(Create(branch) for branch in branches), lag_ratio=0.008), run_time=2.4)
        self.play(FadeIn(generation))
        self.wait(0.35)
