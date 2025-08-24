from manim import *

class CubeRotation(ThreeDScene):
    def construct(self):
        # Set up the camera perspective
        # phi is the angle from the positive Z-axis down (polar angle)
        # theta is the angle from the positive X-axis around the Z-axis (azimuthal angle)
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # Create a Cube object
        # The Cube Mobject is available in Manim
        cube = Cube(
            side_length=2,
            fill_opacity=0.7,
            fill_color=BLUE_D,
            stroke_width=3,
            stroke_color=WHITE
        )

        # Add the cube to the scene
        self.add(cube)

        # Animate the rotation of the cube around different axes
        # Rotate around the Z-axis (OUT vector) by 360 degrees
        self.play(
            Rotate(cube, angle=2 * PI, axis=OUT, run_time=3, rate_func=linear),
            # Add some camera movement for dynamic view
            self.get_moving_camera_rotation(
                phi=70 * DEGREES, theta=0 * DEGREES, run_time=3
            ),
        )
        self.wait(0.5)

        # Rotate around the Y-axis (UP vector) by 360 degrees
        self.play(
            Rotate(cube, angle=2 * PI, axis=UP, run_time=3, rate_func=linear),
            # Reset camera or move it differently
            self.get_moving_camera_rotation(
                phi=45 * DEGREES, theta=-90 * DEGREES, run_time=3
            ),
        )
        self.wait(0.5)

        # Rotate around the X-axis (RIGHT vector) by 360 degrees
        self.play(
            Rotate(cube, angle=2 * PI, axis=RIGHT, run_time=3, rate_func=linear),
            # Another camera angle
            self.get_moving_camera_rotation(
                phi=80 * DEGREES, theta=-20 * DEGREES, run_time=3
            ),
        )
        self.wait(0.5)

        # Rotate around a custom axis (e.g., diagonal)
        custom_axis = normalize(np.array([1, 1, 1])) # Diagonal axis
        self.play(
            Rotate(cube, angle=2 * PI, axis=custom_axis, run_time=4, rate_func=linear),
            # Final camera angle
            self.get_moving_camera_rotation(
                phi=60 * DEGREES, theta=-45 * DEGREES, run_time=4
            ),
        )
        self.wait(1)