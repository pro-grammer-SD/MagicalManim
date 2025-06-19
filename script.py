from manim import *

class Output(Scene):
    def construct(self):
        circle = Circle(radius=2.0, color='#4d9aff')
        self.play(Circumscribe(mobject=circle))
