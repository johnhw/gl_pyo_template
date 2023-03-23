import imgui
import moderngl
import numpy as np
from moderngl_window import geometry
from moderngl_window.opengl.vao import VAO
from moderngl_window.scene import Camera
from pyrr import Matrix44

from audio_fbk import (
    AudioFbk,
    WindFbk,
)

from shader_ui import ShaderCheckbox, ShaderSlider
from window import WindowEvents, iso_now


class DemoEvents(WindowEvents):
    title = "Optimal Mechanism Design / Demo 1"
    author = "JHW"
    aspect_ratio = None

    # map shader name to path to glsl file
    shader_paths = {
        "quad": "shaders/quad.glsl",
        "particles": "shaders/particle.glsl",
        "tex_quad": "shaders/tex_quad.glsl",
    }

    compute_shader_paths = {"particle_dynamics": "shaders/dynamics.glsl"}

    # audio "shaders"
    audio_feedback_map = {
        "None": AudioFbk,
        "Wind": WindFbk,
    }

    # additional arguments
    @classmethod
    def add_arguments(cls, parser):
        super(DemoEvents, cls).add_arguments(parser)
        parser.add_argument(
            "--x",
            "-x",
            default=-1,
            help="Demo x",
        )

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.init_gui()
        self.init_gl()
        self.load_shaders()
        self.init_gui_elements()
        self.alive = False

    def create_particles(self):
        # create the VAO for particle vertices
        self.particles = VAO(name="test", mode=moderngl.POINTS)
        self.positions = np.random.uniform(-1, 1, (64 * 128, 4)).astype(np.float32)
        self.positions[:, 2] = 0.0
        # numpy -> GPU
        self.particle_buf = self.particles.buffer(self.positions, "4f", ["in_position"])

    def init_gl(self):
        # create camera
        self.camera = Camera(
            fov=60.0, aspect_ratio=self.wnd.aspect_ratio, near=0.01, far=10.0
        )
        # self.camera.set_position(0.0, 0.0, 0.0)
        # self.camera.set_rotation(self.camera.yaw, 0.0)

        # create the FBO, geometry and load shaders
        self.fbo_texture = self.ctx.texture((1024, 1024), 3)
        depth = self.ctx.depth_renderbuffer((1024, 1024))
        self.fbo = self.wnd.ctx.framebuffer(self.fbo_texture, depth)
        self.fbo_quad = geometry.quad_2d(size=(0.5, 1), uvs=True)
        self.quad = geometry.quad_2d(size=(2, 2), uvs=True)
        self.deflector_quad = geometry.quad_2d(size=(0.5, 0.5), uvs=True)
        self.create_particles()

    def init_gui_elements(self):
        # UI flags -- these directly set shader
        # uniforms to update values
        self.ui_show_particles = ShaderCheckbox(
            self.shaders["particles"], "show_particles", init_state=True
        )
        self.ui_speed = ShaderSlider(
            self.shaders["particle_dynamics"], "speed", min=0.01, max=4.0, init=1.0
        )

    def update(self):
        super().update()

    def render(self, time: float, frametime: float):
        self.update()

        translation = Matrix44.from_translation((0.0, 0.0, -1.0), dtype="f4")
        model = translation

        # create an FBO to render to
        self.fbo.use()
        # render the background quad
        self.ctx.enable_only(moderngl.BLEND)
        self.quad.render(program=self.shaders["quad"])
        self.ctx.blend_func = self.ctx.DEFAULT_BLENDING

        # # render the particles and update them
        self.ctx.enable_only(moderngl.BLEND)

        self.particles.render(program=self.shaders["particles"])
        self.particle_buf.bind_to_storage_buffer()
        self.shaders["particle_dynamics"].run(64, 1, 1)

        # render the FBO
        self.ctx.screen.use()
        self.fbo_texture.use()

        quad_prog = self.shaders["tex_quad"]
        quad_prog["m_proj"].write(self.camera.projection.matrix)
        quad_prog["m_camera"].write(self.camera.matrix)
        quad_prog["m_model"].write(model)
        self.fbo_quad.render(program=quad_prog)
        self.render_ui()

    def render_ui(self):
        imgui.new_frame()

        # info box
        imgui.begin("Info", closable=False, flags=imgui.WINDOW_NO_TITLE_BAR)
        imgui.text_colored(
            f"{self.title} | {self.author} {iso_now()}", 1.0, 1.0, 1.0, 0.5
        )

        # demo videos should always show the SHA hash of the commit!
        imgui.text_colored(
            f"{self.git['sha']} {self.git['author']} {self.git['date']}",
            0.5,
            0.3,
            0.3,
            0.5,
        )
        imgui.end()

        # main menu
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", "Cmd+Q", False, True
                )
                if clicked_quit:
                    self.close()
                    exit(1)
                imgui.end_menu()
            if imgui.begin_menu("Status", True):
                made_alive, selected_alive = imgui.menu_item(
                    "Alive", "Cmd+A", False, True
                )
                if made_alive:
                    self.alive = True
                made_dead, selected_dead = imgui.menu_item("Dead", "Cmd+A", False, True)
                if made_dead:
                    self.alive = False
                imgui.end_menu()
            imgui.end_main_menu_bar()

        # window controls
        imgui.begin("Controls", True)
        imgui.text_colored("Status", 1.0, 1.0, 1.0, 0.5)

        if not self.alive:
            imgui.text_colored("Dead", 1.0, 0.0, 0.0)
        else:
            imgui.text_colored("Alive", 1.0, 1.0, 1.0)

        imgui.text("ZMQ status")
        imgui.text(self.relay.address)
        if not self.relay.live():
            imgui.text_colored("No ZMQ", 1.0, 0.0, 0.0)
        else:
            imgui.text_colored("ZMQ input!", 1.0, 1.0, 1.0)

        imgui.text_colored("Visuals", 1.0, 1.0, 1.0, 0.5)
        self.ui_speed.slider("Speed")
        # self.ui_show_particles.checkbox("Show particles")

        imgui.text_colored("Audio", 1.0, 1.0, 1.0, 0.5)

        feedback = self.audio_feedbacks.combobox("Audio fbk.")
        if feedback:
            self.set_feedback(feedback)

        # draw the gain sliders and update them
        self.audio.gain_sliders()

        imgui.end()

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def mouse_position_event(self, x, y, dx, dy):
        super().mouse_position_event(x, y, dx, dy)
        w, h = self.wnd.width, self.wnd.height
        self.audio.set_state(x / w, y / h)

    def resize(self, width: int, height: int):
        super().resize(width, height)
        proj = self.camera.projection.matrix
        self.shaders["tex_quad"]["m_proj"].write(proj)
        self.imgui.resize(width, height)


if __name__ == "__main__":
    DemoEvents.run()
