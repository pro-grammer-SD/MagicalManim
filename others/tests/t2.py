from manim import *
from manim.animation.growing import SpinInFromNothing as Sifn

class MyScene(Scene):
    def construct(self):
        c = Circle(color=DARK_BLUE)
        self.play(Sifn(c, 40, "green"))
        s = Square(side_length=7, color=PINK)
        self.play(Transform(c, s))
        
MyScene().render(True)
