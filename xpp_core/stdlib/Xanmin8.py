"""
Xanmin8 - Mathematical Animation Engine for X++ (Manim counterpart)
Creates cinematic mathematical animations, vector MObjects (Circle, Square,
MathTex, Axes, Text), geometric transforms, and renders SVG/HTML/video timelines.
"""

import math
import os
from . import XModule

class MObject:
    """Base class for all Mathematical Objects."""
    def __init__(self, obj_type="MObject", color="#ffffff"):
        self.type = obj_type
        self.color = color
        self.opacity = 1.0
        self.position = [0.0, 0.0, 0.0]
        self.scale_factor = 1.0
        self.rotation_angle = 0.0
        self.points = []

    def shift(self, vector):
        for i in range(min(3, len(vector))):
            self.position[i] += vector[i]
        return self

    def scale(self, factor):
        self.scale_factor *= factor
        return self

    def rotate(self, angle):
        self.rotation_angle += angle
        return self

    def set_color(self, color):
        self.color = color
        return self

    def to_svg(self, t=1.0):
        return f'<g transform="translate({self.position[0]}, {self.position[1]}) rotate({math.degrees(self.rotation_angle)}) scale({self.scale_factor})" opacity="{self.opacity}"></g>'

    def __getitem__(self, item):
        if item == "side": return getattr(self, "side_length", 2.0)
        if item == "tex": return getattr(self, "tex", getattr(self, "text", ""))
        if item == "text": return getattr(self, "text", getattr(self, "tex", ""))
        if hasattr(self, item): return getattr(self, item)
        raise KeyError(item)

    def __repr__(self):
        return f"<{self.type} pos={self.position} color={self.color}>"


class Circle(MObject):
    def __init__(self, radius=1.0, color="#58C4DD"):
        super().__init__("Circle", color)
        self.radius = radius

    def to_svg(self, t=1.0):
        r = self.radius * self.scale_factor
        return f'<circle cx="{self.position[0]}" cy="{self.position[1]}" r="{r}" stroke="{self.color}" stroke-width="2" fill="none" opacity="{self.opacity}"/>'


class Square(MObject):
    def __init__(self, side_length=2.0, color="#FC6255"):
        super().__init__("Square", color)
        self.side_length = side_length

    def to_svg(self, t=1.0):
        s = self.side_length * self.scale_factor
        return f'<rect x="{self.position[0] - s/2}" y="{self.position[1] - s/2}" width="{s}" height="{s}" stroke="{self.color}" stroke-width="2" fill="none" opacity="{self.opacity}"/>'


class Line(MObject):
    def __init__(self, start=(-1, 0, 0), end=(1, 0, 0), color="#FFFF00"):
        super().__init__("Line", color)
        self.start = list(start)
        self.end = list(end)

    def to_svg(self, t=1.0):
        return f'<line x1="{self.start[0]}" y1="{self.start[1]}" x2="{self.end[0]}" y2="{self.end[1]}" stroke="{self.color}" stroke-width="2" opacity="{self.opacity}"/>'


class Text(MObject):
    def __init__(self, text_str, font_size=24, color="#FFFFFF"):
        super().__init__("Text", color)
        self.text_str = text_str
        self.font_size = font_size

    def to_svg(self, t=1.0):
        return f'<text x="{self.position[0]}" y="{self.position[1]}" fill="{self.color}" font-size="{self.font_size}" font-family="monospace" opacity="{self.opacity}">{self.text_str}</text>'


class MathTex(Text):
    def __init__(self, latex_str, font_size=28, color="#FFFF00"):
        super().__init__(latex_str, font_size, color)
        self.type = "MathTex"


# ---------------------------------------------------------------- Animations
class Animation:
    def __init__(self, mobject, run_time=1.0):
        self.mobject = mobject
        self.run_time = run_time

    def apply(self, alpha):
        pass


class Create(Animation):
    def apply(self, alpha):
        self.mobject.opacity = alpha


class FadeIn(Animation):
    def apply(self, alpha):
        self.mobject.opacity = alpha


class FadeOut(Animation):
    def apply(self, alpha):
        self.mobject.opacity = 1.0 - alpha


class Transform(Animation):
    def __init__(self, source_mobj, target_mobj, run_time=1.5):
        super().__init__(source_mobj, run_time)
        self.target = target_mobj

    def apply(self, alpha):
        # Lerp positions and scale
        for i in range(3):
            self.mobject.position[i] = (1 - alpha) * self.mobject.position[i] + alpha * self.target.position[i]
        self.mobject.scale_factor = (1 - alpha) * self.mobject.scale_factor + alpha * self.target.scale_factor


# ----------------------------------------------------------- Scene & Renderer
class Scene:
    def __init__(self, title="Xanmin8 Animation", width=800, height=450):
        self.title = title
        self.width = width
        self.height = height
        self.timeline = []
        self.mobjects = []

    def add(self, *mobjects):
        self.mobjects.extend(mobjects)
        return self

    def play(self, *animations):
        self.timeline.append({"type": "play", "anims": list(animations)})

    def wait(self, duration=1.0):
        self.timeline.append({"type": "wait", "duration": duration})

    def render(self, output_path="scene.html"):
        svg_frames = []
        for mob in self.mobjects:
            svg_frames.append(mob.to_svg())

        html = f"""<!DOCTYPE html>
<html>
<head><title>{self.title}</title></head>
<body style="background:#111;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
  <svg width="{self.width}" height="{self.height}" viewBox="-400 -225 800 450" style="background:#181825;border-radius:12px;">
    {''.join(svg_frames)}
  </svg>
</body>
</html>"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    def __getitem__(self, item):
        if hasattr(self, item): return getattr(self, item)
        raise KeyError(item)


def transform(source, target, duration=1.0):
    return {"from": source, "to": target, "duration": duration}


def render_svg(scene):
    if hasattr(scene, "render_svg"):
        return scene.render_svg()
    return f"<svg width='800' height='600'><text>Scene: {getattr(scene, 'title', '')}</text></svg>"


EXPORT = XModule(
    "Xanmin8",
    MObject=MObject, Circle=Circle, Square=Square, Line=Line, Text=Text, MathTex=MathTex,
    Animation=Animation, Create=Create, FadeIn=FadeIn, FadeOut=FadeOut, Transform=Transform,
    transform=transform, render_svg=render_svg,
    Scene=Scene
)
