from manim import *

class Output(Scene):
    def construct(self):
        circle = Circle(radius=2.0, color='#79ffea')
        arrowsquarefilledtip = ArrowSquareFilledTip(fill_opacity=1.0, stroke_width=0.0, color='#47ff04')
        self.play(Create(mobject=circle, lag_ratio=1.0, introducer='True'))
        self.play(Create(mobject=arrowsquarefilledtip, lag_ratio=1.0, introducer='True'))
        self.interactive_embed()