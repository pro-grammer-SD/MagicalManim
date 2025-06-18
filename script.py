from manim import *

class Output(Scene):
    def construct(self):
        self.interactive_embed()
        circle = Circle(radius=1, color=BLUE)
        self.play(Create(mobject=circle, lag_ratio=1.0, introducer='True'))