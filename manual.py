import numpy as np
import sounddevice as sd
import time


sampleRate = 44100
duration = 20
freq = 300
class WaveStreamer:
    def __init__(self, amplitude, freq):
        self.l = 0
        self.amplitude = amplitude
        self.freq = freq
        self.waveform = np.sin(2 * np.pi * np.arange(sampleRate * duration) * (freq / sampleRate)).reshape(-1, 1)
        self.stream = sd.OutputStream(samplerate=sampleRate, channels=2, blocksize= 256, callback=self.streamCallback)

    def getNextData(self, frames):
        r = self.l + frames
        block = self.waveform[self.l:r]
        self.l = r
        return block * self.amplitude

    def streamCallback(self, outdata, frames, time, status):
        if status:
            print(f'{status=}')
        
        block = self.getNextData(frames)
        if (len(block) >= frames):
            outdata[:] = block 
        else:
            outdata[:len(block)] = block
            outdata[len(block):] = 0
            self.l = 0

    def setAmplitude(self, amplitude):
        self.amplitude = amplitude

    def start(self):
        self.stream.start()
    def stop(self):
        self.stream.stop()

def main():
    arr = np.arange(sampleRate * duration)

    sine = WaveStreamer(0.2, 300)
    sine.start()
    #time.sleep(duration/2)
    time.sleep(2)
    print(f'set amp')
    sine.setAmplitude(0.7)
    time.sleep(2)
    #time.sleep(duration/2)
    sine.stop()


main()
