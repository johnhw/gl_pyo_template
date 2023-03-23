import moderngl_window as mlgw
from time import perf_counter
import git
from zmq_relay import Relay
from moderngl_window.integrations.imgui import ModernglWindowRenderer
import time
from datetime import datetime
from dateutil import tz
from audio_fbk import AudioServer
from pathlib import Path
from shader_ui import ComboList
import imgui


def iso_now():
    return datetime.now(tz=tz.tzlocal()).isoformat()


class WindowEvents(mlgw.WindowConfig):
    gl_version = (4, 3)
    title = "OVERRIDE title"
    author = "OVERRIDE author"
    resource_dir = (Path(__file__).parent).resolve()
    aspect_ratio = None

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
        self.audio_feedbacks = ComboList(self.audio_feedback_map)

        self.audio = None
        # use command line arg for initial connection
        self.set_feedback(self.audio_feedbacks.dict[self.argv.audio])

    def init_zmq(self):
        self.relay = Relay()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_audio()
        self.init_git()
        self.init_zmq()
        self.init_t = perf_counter()
        self.alive = False

    def update(self):
        # poll ZMQ
        self.relay.poll()
        t = perf_counter() - self.init_t
        # copy time into every shader
        for shader in self.shaders.values():
            if "iTime" in shader:
                shader["iTime"] = t

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
