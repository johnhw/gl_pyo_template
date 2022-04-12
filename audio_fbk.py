import imgui
import numpy as np
import pyo
import sys
from datetime import datetime
from audio_utils import fdb

# note: to avoid glitches in audio, do not set values on pyo
# objects directly during interaction.
#
# Instead, create a pyo.SigTo object, and use that as the value input.
# Then, update the SigTo using setValue(new_value); this will induce
# a smooth transition in state. The response time of the SigTo
# can be configured (the default of 25ms is good for most purposes)


class AudioServer:
    def __init__(self, audio=False, device=-1, server="pa", winhost="mme"):

        # boot the server
        if audio == False:
            # no audio in this case
            self.server = pyo.Server(audio="offline_nb")
        else:
            if sys.platform == "win32":
                self.server = pyo.Server(winhost=winhost, audio=server)
            else:
                self.server = pyo.Server(audio=server)

            # set audio id requested
            if device != -1:
                self.server.setOutputDevice(device)
        self.server.boot().start()
        # make sure we know we are alive
        # play a startup sound
        self.startup = pyo.SfPlayer(
            "sounds/startup.wav", loop=False, speed=1, mul=0.4
        ).out()

    def close(self):
        # kill the audio
        self.server.stop()
        self.server.shutdown()

    def stop(self):
        self.server.stop()

    def start(self):
        self.server.start()


class AudioFbk:
    def __init__(self, server):
        self.server = server.server
        self.gains = {}

    def add_gain(self, name, elt, gain=0.0):
        """Register a decibel gain for a given
        element. Sets the elements mul
        property based on inputs from a slider
        (specified in dB)"""
        self.gains[name] = (gain, elt)

    def gain_sliders(self):
        """Create sliders for any adjustable gains"""
        for name in self.gains:
            db, elt = self.gains[name]
            _, db = imgui.slider_float(name.title() + " dB", db, -40, 0.0, "%.0f", 1.0)
            self.gains[name] = (db, elt)
            elt.mul = fdb(db)


class WindFbk(AudioFbk):
    """Noise generator with moving
    resonant filter"""

    def __init__(self, server):
        super().__init__(server)

        self.noise = pyo.Noise()
        self.freq = pyo.SigTo(1000.0)
        self.q = pyo.SigTo(2.0)
        self.lp_freq = pyo.SigTo(1000.0)
        self.lp_filter = pyo.Biquad(self.noise, freq=self.lp_freq)
        self.filter = pyo.Resonx(self.lp_filter, freq=self.freq, q=self.q)

        self.main_gain = pyo.SigTo(0.0, time=0.1)
        self.delay = pyo.Delay(
            self.filter * self.main_gain * 2.0, feedback=0.2, delay=0.4
        )
        self.compressor = pyo.Compress(self.delay)
        self.out = self.compressor
        self.out.out()

    def set_rate(self, rate, x, y):
        y = float(np.tanh(y * 2.0))
        self.lp_freq.setValue((1 - y) * 1000.0)
        self.main_gain.setValue(float(np.tanh(rate) * 0.4))
        self.freq.setValue(1000.0 * float(np.exp((x - 0.5) * 3.0)))
        self.q.setValue(2 * (1 - y))
