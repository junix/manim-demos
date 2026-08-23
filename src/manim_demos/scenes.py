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
    rule = Line(subtitle_text.get_left() + DOWN * 0.18, subtitle_text.get_left() + RIGHT * 3.7 + DOWN * 0.18, color="#4e7187", stroke_width=1.4)
    return VGroup(title_text, subtitle_text, rule)


class AlgorithmTrace(Scene):
    def construct(self) -> None:
        header = title_block("BINARY SEARCH / TRACE 06", "INTERVAL HALVING AS A VISUAL INVARIANT")
        values = [3, 8, 12, 19, 24, 31, 42, 47, 58, 63, 71, 86, 91]
        cards = VGroup()
        for index, value in enumerate(values):
            box = RoundedRectangle(width=0.78, height=0.72, corner_radius=0.1, stroke_color="#6689a0", stroke_width=1.5, fill_color="#132740", fill_opacity=0.78)
            number = Text(str(value), font="Avenir Next", font_size=22, color=INK)
            card = VGroup(box, number)
            card.move_to(LEFT * 5.2 + RIGHT * index * 0.86 + UP * 0.35)
            cards.add(card)
        target = VGroup(Circle(radius=0.37, color=ROSE, stroke_width=3.2), Text("42", font="Avenir Next", font_size=20, color=ROSE)).arrange()
        target_label = Text("TARGET", font="Avenir Next", font_size=13, color=MUTED).next_to(target, UP, buff=0.15)
        target_group = VGroup(target_label, target).move_to(RIGHT * 4.7 + UP * 2.05)
        tracks = VGroup()
        intervals = [(0, 12, 6, "mid = 6"), (0, 5, 2, "mid = 2"), (3, 5, 4, "mid = 4"), (5, 5, 5, "found")]
        for row, (lo, hi, mid, note) in enumerate(intervals):
            y = -0.75 - row * 0.85
            start = cards[lo].get_center()[0]
            end = cards[hi].get_center()[0]
            line = Line([start, y, 0], [end, y, 0], color=[CYAN, INDIGO, AMBER, ROSE][row], stroke_width=6 - row * 0.65)
            left_tick = Line([start, y - 0.13, 0], [start, y + 0.13, 0], color=line.get_color())
            right_tick = Line([end, y - 0.13, 0], [end, y + 0.13, 0], color=line.get_color())
            dot = Dot([cards[mid].get_center()[0], y, 0], radius=0.09, color=AMBER if row < 3 else ROSE)
            note_text = Text(note, font="Avenir Next", font_size=15, color=INK).next_to(right_tick, RIGHT, buff=0.18)
            tracks.add(VGroup(line, left_tick, right_tick, dot, note_text))
        caption = Text("Each comparison preserves:  target ∈ [low, high]", font="Avenir Next", font_size=18, color=CYAN).to_edge(DOWN, buff=0.42)
        self.play(FadeIn(header), LaggedStart(*(FadeIn(card, shift=UP * 0.12) for card in cards), lag_ratio=0.045), run_time=1.2)
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
            arrow = Arrow(point, end, buff=0, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.12)
            chains.add(circle, arrow, Dot(end, radius=0.055, color=color))
            point = end
        axes = Axes(x_range=[0, 6, 1], y_range=[-2.3, 2.3, 1], x_length=5.5, y_length=4.4, axis_config={"color": "#57768d", "stroke_opacity": 0.7, "include_ticks": False}).move_to(RIGHT * 3.35 + DOWN * 0.15)
        wave = axes.plot(lambda x: 1.55 * np.sin(x + time) + 0.72 * np.sin(3 * (x + time)) + 0.43 * np.sin(5 * (x + time)) + 0.3 * np.sin(7 * (x + time)), x_range=[0, 6, 0.025], color=ROSE, stroke_width=3)
        bridge = Line(point, axes.c2p(0, 1.55 * np.sin(time) + 0.72 * np.sin(3 * time) + 0.43 * np.sin(5 * time) + 0.3 * np.sin(7 * time)), color="#b9cfdd", stroke_width=1.2, stroke_opacity=0.6)
        legend = VGroup(*[VGroup(Dot(color=c), Text(f"n = {f}", font="Avenir Next", font_size=15, color=INK)).arrange(RIGHT, buff=0.13) for f, c in zip(frequencies, colors, strict=True)]).arrange(RIGHT, buff=0.48).to_edge(DOWN, buff=0.42)
        self.play(FadeIn(header), LaggedStart(*(Create(item) for item in chains), lag_ratio=0.08), run_time=1.5)
        self.play(Create(axes), Create(bridge), Create(wave), run_time=1.6)
        self.play(FadeIn(legend))
        self.wait(0.5)


class GeometricProof(Scene):
    def construct(self) -> None:
        header = title_block("PYTHAGORAS / REARRANGEMENT", "THE SAME FOUR TRIANGLES, TWO INTERIORS")
        colors = [CYAN, INDIGO, ROSE, AMBER]
        panels = VGroup()
        for panel_x, mode in ((-3.45, "c²"), (3.45, "a² + b²")):
            frame = Square(side_length=4.35, color="#6c8aa0", stroke_width=1.8, fill_color="#11263d", fill_opacity=0.42).move_to([panel_x, -0.35, 0])
            tris = VGroup()
            base = np.array([[-2.05, -2.05, 0], [0.55, -2.05, 0], [-2.05, -0.45, 0]])
            for i in range(4):
                tri = Polygon(*base, color=colors[i], stroke_width=2, fill_color=colors[i], fill_opacity=0.27)
                tri.rotate(i * PI / 2, about_point=ORIGIN).shift([panel_x, -0.35, 0])
                tris.add(tri)
            if mode == "c²":
                inner = Square(side_length=1.72, color=VIOLET, stroke_width=2.6, fill_color="#4a2c64", fill_opacity=0.42).rotate(0.56).move_to([panel_x, -0.35, 0])
                label = Text("c²", font="Avenir Next", weight="BOLD", font_size=31, color=VIOLET).move_to(inner)
            else:
                inner_a = Rectangle(width=1.55, height=1.55, color=CYAN, stroke_width=2.5, fill_color="#19413e", fill_opacity=0.55).move_to([panel_x - 0.82, -0.35, 0])
                inner_b = Rectangle(width=1.08, height=1.08, color=AMBER, stroke_width=2.5, fill_color="#493d1d", fill_opacity=0.55).move_to([panel_x + 0.75, -0.35, 0])
                inner = VGroup(inner_a, inner_b)
                label = VGroup(Text("a²", font="Avenir Next", font_size=26, color=CYAN).move_to(inner_a), Text("b²", font="Avenir Next", font_size=24, color=AMBER).move_to(inner_b))
            panels.add(VGroup(frame, tris, inner, label))
        equality = Text("SAME OUTER AREA  −  SAME TRIANGLES", font="Avenir Next", font_size=17, color=MUTED).to_edge(DOWN, buff=0.58)
        therefore = Text("c²  =  a² + b²", font="Avenir Next", weight="BOLD", font_size=28, color=INK).next_to(equality, UP, buff=0.18)
        self.play(FadeIn(header), Create(panels[0][0]), Create(panels[1][0]))
        self.play(LaggedStart(*(FadeIn(panel[1], shift=UP * 0.1) for panel in panels), lag_ratio=0.25), run_time=1.5)
        self.play(FadeIn(panels[0][2:]), FadeIn(panels[1][2:]))
        self.play(FadeIn(therefore), FadeIn(equality))
        self.wait(0.5)
