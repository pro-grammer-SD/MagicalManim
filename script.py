from manim import *

class Output(Scene):
    def construct(self):
        circle = Circle(radius=2, color='#ff9c04')
        self.play(Create(mobject=circle, lag_ratio=1.0, introducer='True'))
        self.interactive_embed()