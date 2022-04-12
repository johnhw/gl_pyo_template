import time
from datetime import datetime
from dateutil import tz
from pathlib import Path
from time import perf_counter, sleep
import rich


import git
import imgui
import moderngl
import moderngl_window as mglw
import numpy as np
from moderngl_window import geometry
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.opengl.vao import VAO
from moderngl_window.scene import Camera
from pyrr import Matrix44
from zmq_relay import Relay

from audio_fbk import (
    AudioServer,
    AudioFbk,
    WindFbk,
)

from shader_ui import ShaderCheckbox, ShaderSlider, ComboList

TITLE = "CHANGE ME"
AUTHOR = "JHW"


def iso_now():
    return datetime.now(tz=tz.tzlocal()).isoformat()


class WindowEvents(mglw.WindowConfig):
    gl_version = (4, 3)
    title = TITLE
    resource_dir = (Path(__file__).parent).resolve()
    aspect_ratio = None

    # map shader name to path to glsl file
    shader_paths = {
        "quad": "shaders/quad.glsl",
        "particles": "shaders/particle.glsl",
        "tex_quad": "shaders/tex_quad.glsl",
    }

    compute_shader_paths = {"particle_dynamics": "shaders/dynamics.glsl"}

    def create_particles(self):
        # create the VAO for particle vertices
        self.particles = VAO(name="test", mode=moderngl.POINTS)
        self.positions = np.random.uniform(-1, 1, (64 * 128, 4)).astype(np.float32)
        self.positions[:, 2] = 0.0
        # numpy -> GPU
        self.particle_buf = self.particles.buffer(self.positions, "4f", ["in_position"])

    def get_projection(self):
        return self.camera.projection.matrix  # proj

    def close(self):        
        self.relay.close()
        time.sleep(0.1)
        self.audio_server.close()
        time.sleep(0.1)
        exit()

    def load_shaders(self):
        # load all of the shaders into a dictionary
        self.shaders = {}
        for shader, path in self.shader_paths.items():
            print(path)
            self.shaders[shader] = self.load_program(path)

        for shader, path in self.compute_shader_paths.items():
            self.shaders[shader] = self.load_compute_shader(path)

    def set_feedback(self, fbk):
        """Set the feedback type to the given value"""
        if self.audio is not None:
            del self.audio
        self.audio_server.stop()
        time.sleep(0.05)
        self.audio_server.start()
        self.audio = fbk(self.audio_server)

    @classmethod
    def add_arguments(self, parser):
        # we can add any arguments to the cmd line here
        # ZMQ port
        parser.add_argument(
            "--port",
            "-p",
            default=5556,
            help="Set the port to listen on for incoming ZMQ messages",
        )
        parser.add_argument(
            "--audio",
            "-a",
            default="Wind",
            help="Set the initial audio feedback used on startup",
        )

        parser.add_argument(
            "--device",
            "-d",
            default=-1,
            help="Set the PortAudio device number used for audio feedback",
        )
        parser.add_argument(
            "--audio_server",
            default="pa",
            help="Set the server to use (portaudio, jack or coreaudio)",
        )

    def init_git(self):
        # get current git details
        head = git.Repo(search_parent_directories=True).head.commit
        self.git = {
            "sha": head.hexsha,
            "date": datetime.fromtimestamp(head.committed_date).isoformat(),
            "author": head.author.name,
        }

    def init_gui(self):
        # construct the window image
        imgui.create_context()

        # initialise window and audio
        self.imgui = ModernglWindowRenderer(self.wnd)

    def init_audio(self):
        self.audio_server = AudioServer(
            audio=True, device=int(self.argv.device), server=self.argv.audio_server
        )
        self.audio_feedbacks = ComboList(
            {
                "None": AudioFbk,
                "Wind": WindFbk,
            }
        )
        self.audio = None
        # use command line arg for initial connection
        self.set_feedback(self.audio_feedbacks.dict[self.argv.audio])

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
        self.load_shaders()

    def init_gui_elements(self):
        # UI flags -- these directly set shader
        # uniforms to update values
        self.ui_show_particles = ShaderCheckbox(
            self.shaders["particles"], "show_particles", init_state=True
        )
        self.ui_speed = ShaderSlider(
            self.shaders["particle_dynamics"], "speed", min=0.01, max=4.0, init=1.0
        )

    def init_zmq(self):
        self.relay = Relay()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_git()
        self.init_audio()
        self.init_gui()
        self.init_gl()
        self.init_gui_elements()
        self.init_zmq()
        self.init_t = perf_counter()
        self.alive = False

    def render(self, time: float, frametime: float):

        translation = Matrix44.from_translation((0.0, 0.0, -1.0), dtype="f4")
        model = translation
        t = perf_counter() - self.init_t

        # copy time into every shader
        for shader in self.shaders.values():
            if "iTime" in shader:
                shader["iTime"] = t

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
        imgui.text_colored(f"{TITLE} | {AUTHOR} {iso_now()}", 1.0, 1.0, 1.0, 0.5)

        # demo videos should always show the SHA hash of the commit!
        imgui.text_colored(
            f"{self.git['sha']} {self.git['author']} {self.git['date']}",
            0.3,
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
            imgui.text_colored(f"Alive", 1.0, 1.0, 1.0)

        imgui.text("ZMQ status")
        imgui.text(self.relay.address)
        if not self.relay.live():
            imgui.text_colored("No ZMQ", 1.0, 0.0, 0.0)
        else:
            imgui.text_colored(f"ZMQ input!", 1.0, 1.0, 1.0)

        imgui.text_colored("Visuals", 1.0, 1.0, 1.0, 0.5)
        self.ui_speed.slider("Speed")
        #self.ui_show_particles.checkbox("Show particles")

        imgui.text_colored("Audio", 1.0, 1.0, 1.0, 0.5)

        feedback = self.audio_feedbacks.combobox("Audio fbk.")
        if feedback:
            self.set_feedback(feedback)

        # draw the gain sliders and update them
        self.audio.gain_sliders()

        imgui.end()

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    # forward all window events to pyimgui
    def key_event(self, key, action, modifiers):        
        self.imgui.key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)

    def resize(self, width: int, height: int):
        proj = self.get_projection()
        self.shaders["tex_quad"]["m_proj"].write(proj)
        self.imgui.resize(width, height)


if __name__ == "__main__":
    WindowEvents.run()
