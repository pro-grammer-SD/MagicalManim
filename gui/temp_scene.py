from manim import *

class Output(Scene):
    def construct(self):
        annulus = Annulus(inner_radius='1', outer_radius='2', fill_opacity='1', stroke_width='0', color='#f23aff')
        self.play(Transform(mobject='', target_mobject='None', path_func='None', path_arc='0', path_arc_axis='array([0., 0., 1.])', path_arc_centers='None', replace_mobject_with_target_in_scene='False'))