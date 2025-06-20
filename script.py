from manim import *

class Output(Scene):
    def construct(self):
        circle = Circle(radius=3.0, color='#ff04ff')
        self.play(Create(mobject=circle, lag_ratio=1.0, introducer='True'))
        self.interactive_embed()