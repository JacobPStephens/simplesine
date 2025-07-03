import math, threading, os, time
import numpy as np
import sounddevice as sd
import tkinter as tk
import utils

os.system('xset r off')
NOTE_TO_PITCH = {
    'a': (-3, 220),
    'a#': (-2,0),
    'bb': (-2, 0),
    'b': (-1, 246.9),
    'c': (0, 261.6),
    'c#': (1, 0),
    'db': (1, 0),
    'd': (2, 293.7),
    'd#': (3, 0),
    'eb': (3, 0),
    'e': (4, 329.6),
    'f': (5, 349.2),
    'f#': (6, 0),
    'gb': (6, 0),
    'g': (7, 392.0),
    'g#': (8, 0),
    'ab': (8, 0)}
sampleRate = 48000
duration = 3
sines = []
rawAmps = dict()
normalizedAmps = dict()

attack = 2
decay = 1
sustainVolume = utils.decibelsToAmplitude(-10)
maxVolume = utils.decibelsToAmplitude(-5)
release = 2

class WaveStreamer:
    def __init__(self, amplitude, freq):
        self.l = 0
        self.phase = 0
        self.amplitude = amplitude
        self.freq = freq
        self.stream = sd.OutputStream(samplerate=sampleRate, channels=2, blocksize= 256, callback=self.streamCallback)

    def getNextData(self, frames):
        t = (np.arange(frames) + self.phase) / sampleRate
        block = self.amplitude * np.sin(2 * np.pi * self.freq * t).reshape(-1, 1)
        self.phase = (self.phase + frames) % (sampleRate / self.freq) # wrap num samples
        return block

    def streamCallback(self, outdata, frames, time, status):
        if status: print(f'{status=}')
        # get next block of samples and output to stream
        block = self.getNextData(frames)
        outdata[:] = np.repeat(block, 2, axis=1)



def main():
    # start
    normalizeThread = threading.Thread(target=normalize)
    normalizeThread.start()

    # update
    while True:
        normalizeThread
        for sine in rawAmps:
            print(sine.amplitude)
        ##print(rawAmps)
        time.sleep(1)
    

def normalize():

    while True:
        totalRawAmps = sum(rawAmps.values()) + 0.1

        for s in rawAmps:
            if totalRawAmps <= 1:
                normalizedAmps[s] = rawAmps[s]
                
            else:
                normalizedAmps[s] = (rawAmps[s] / totalRawAmps)  

            s.amplitude = normalizedAmps[s]
        ##print(f'Raw   ={rawAmps.values()}')
        ##print(f'Normal={normalizedAmps.values()}')
        time.sleep(0.005)


def fade(sine: WaveStreamer, note: str, startVolume: float, endVolume:float, duration: float, stage: str):
    start = time.time()
    t = 0
    while t < duration:
        if (stage == "a" or stage == "d") and ((sine, note) not in sines):
            return
        
        # continuously calculate volume based on time 
        volume = startVolume + ((endVolume - startVolume) * (t / duration))
        rawAmps[sine] = volume
        t = time.time() - start
        time.sleep(0.01)

    # end behavior based on stage
    if (stage == "a") and ((sine, note) in sines):
        print("Attack finished. Initiating Decay")
        decayThread = threading.Thread(target=fade, args=[sine, note, maxVolume, sustainVolume, decay, "d"])
        decayThread.start()
    elif (stage == "d"):
        print("Decay finished")
    
    elif (stage == "r"):
        #print(f'Release completed. At silence.')   
        del rawAmps[sine]
        del normalizedAmps[sine]  
        sine.stream.stop()



def playNote(c: str):

    sine = WaveStreamer(amplitude=0.5, freq=NOTE_TO_PITCH[c][1])
    sines.append((sine, c))
    attackThread = threading.Thread(target=fade, args=[sine, c, 0, maxVolume, attack, "a"])
    attackThread.start()

    sine.stream.start()

def onKeyPressed(event):

    print(f'{event.char} pressed')
    c = event.char
    if (c not in NOTE_TO_PITCH):
        return
    
    playNote(c)

def onKeyReleased(event):
    print(f'{event.keysym} released')
    for (sine, c) in sines:
        if c == event.keysym:
            print("Initiating Release.")
            currentVolume = sine.amplitude
            releaseThread = threading.Thread(target=fade, args=[sine, c, currentVolume, 0, release, "r"])
            releaseThread.start()
            sines.remove((sine, c))




updateThread = threading.Thread(target=main)
updateThread.start()
##print('normalize thread started')



root = tk.Tk()
root.title("My tkinter window")
root.geometry("400x300+100+50")
root.bind("<KeyPress>", onKeyPressed)
root.bind("<KeyRelease>", onKeyReleased)
root.mainloop()
os.system('xset r on')