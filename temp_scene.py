from manim import *

class Output(Scene):
    def construct(self):
        circle = Circle(radius=1.3, color='#00ff7f')
        self.play(Create(mobject=circle, lag_ratio=1.0, introducer=True))