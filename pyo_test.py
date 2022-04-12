import sys, time
from pyo import *


print("* Checking for any available audio output... *")

output_names, output_indexes = pa_get_output_devices()
print("Found output devices:")
print("\n".join([f"\t {ix}:{name}" for ix, name in zip(output_indexes, output_names)]))

print("* Checking audio output hosts... *")

s = Server(duplex=0)
s.verbosity = 0
for name, ix in zip(output_names, output_indexes):
    print(f"Testing output device {name}...")
    s.reinit(buffersize=1024, duplex=0)
    s.setOutputDevice(ix)
    s.boot().start()
    a = Sine(freq=440, mul=0.2).out()
    time.sleep(1)
    s.stop()
    s.shutdown()
