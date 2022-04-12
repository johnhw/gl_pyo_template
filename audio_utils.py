import pyo
import numpy
from datetime import datetime

# Some basic transfer functions
def fdb(db):
    """Convert a decibel value to a float"""
    return 10 ** (db / 10.0)


def midi_to_freq(m):
    return 440 * 2 ** ((m - 69) / 12.0)


def sigmoid(x):
    return 1.0 / (1 + np.exp(-x))


def squanch(x, ctr=0.5, shape=1.0, sign=1):
    """
    Saturating curve, input in [0,1], output in [0,1]
    centred on ctr. shape determines sharpness
    sign inverts direction if = -1.
    """
    return float(0.5 + 0.5 * sign * np.tanh((x - ctr) * shape))


def make_granulator(snd_file):
    """Construct a synchronous
    granulator object from a given sound file"""
    base_sound = pyo.SndTable(snd_file)
    env = pyo.WinTable(0)  # env. turned off
    # slight randomised pitcch
    ptch = pyo.Randi(min=0.95, max=1.05, freq=100)
    gr = pyo.Granule(base_sound, env, dens=2.0, pitch=ptch, mul=0.01, dur=0.1)
    return gr


def texture_granulator(snd_file, dur=0.25):
    """Construct a dense asynchronous
    granulator object from a given sound file"""
    base_sound = pyo.SndTable(snd_file)
    env = pyo.HannTable()  # smooth grains
    end = base_sound.getSize() - dur * 44100
    pos = pyo.Randi(min=0, max=1, freq=[0.25, 0.3], mul=end)
    smoother = pyo.SigTo(0.0, time=0.016)
    # dense cloud, and not synchronised
    gr = pyo.Granule(base_sound, env, dens=20.0, mul=smoother, pos=pos, dur=dur)
    gr.setSync(False)
    return gr, smoother


class SampleVoices:
    """Manage polyphony when playing multiple samples,
    by using the least recently used sample player to
    trigger a sample"""

    def __init__(self, n=32):
        self.n = n
        self.dummy_tab = pyo.HannTable()
        self.voices = [
            (datetime.now(), pyo.TableRead(self.dummy_tab, freq=2)) for i in range(n)
        ]

    def play(self, tab, mul=1.0):
        self.voices.sort()
        dt, voice = self.voices[0]
        voice.stop()
        voice.mul = float(mul)
        voice.freq = tab.getRate()
        voice.reset()
        voice.setTable(tab)
        voice.play()
        self.voices[0] = (datetime.now(), voice)

    def get_output(self):
        return sum([voice for dt, voice in self.voices])
