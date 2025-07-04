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

attack = 1
decay = 0.25
minDecay = 0
maxDecay = 2
maxVolume = utils.decibelsToAmplitude(-2)
sustain = utils.decibelsToAmplitude(-10)
minSustain = 0
maxSustain = maxVolume
release = 2
minRelease = 0
maxRelease = 8
minAttack = 0
maxAttack = 8

class WaveStreamer:
    def __init__(self, amplitude, freq):
        self.l = 0
        self.phase = 0
        self.amplitude = amplitude
        self.freq = freq
        self.stream = sd.OutputStream(samplerate=sampleRate, channels=2, blocksize = 1024, callback=self.streamCallback)

    def getNextData(self, frames):
        t = (np.arange(frames) + self.phase) / sampleRate
        block = self.amplitude * np.sin(2 * np.pi * self.freq * t).reshape(-1, 1)
        self.phase += frames
        return block

    def streamCallback(self, outdata, frames, time, status):
        if status: print(f'{status=}')
        # get next block of samples and output to stream
        block = self.getNextData(frames)
        #block = np.clip(block, -1.0, 1.0)
        outdata[:] = np.repeat(block, 2, axis=1)

class Dials:
    def __init__(self, arc):
        self.arc = arc
        self.mouse_x: int = 0
        self.mouse_y: int = 0
        self.activeDial: str | None = None
        self.clickOrigin: tuple = None
    
    def mouseMotion(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        
        if not self.activeDial:
            return
        
        difference = self.clickOrigin[1] - self.mouse_y
        difference = max(-50, difference)
        difference = min(50, difference)

        self.adjustArcAndValue(difference)
        

    def adjustArcAndValue(self, difference):
        global attack, decay, sustain, release
        arcAngle = ((difference + 50) / 100.01) * -360

        if self.activeDial == "attack":
            attack = minAttack + (maxAttack - minAttack) * (abs(arcAngle) / 360)
            canvas.itemconfig(attackArc, extent=arcAngle)
            canvas.itemconfig(attackText, text=f'{attack:.2f}')

        elif self.activeDial == "decay":
            decay = minDecay + (maxDecay - minDecay) * (abs(arcAngle) / 360)
            canvas.itemconfig(decayArc, extent=arcAngle)
            canvas.itemconfig(decayText, text=f'{decay:.2f}') 

        elif self.activeDial == "sustain":
            sustain = minSustain + (maxSustain - minSustain) * (abs(arcAngle) / 360)
            canvas.itemconfig(sustainArc, extent=arcAngle)
            canvas.itemconfig(sustainText, text=f'{utils.amplitudeToDecibels(sustain):.2f}dB')  

        elif self.activeDial == "release":
            release = minRelease + (maxRelease - minRelease) * (abs(arcAngle) / 360)
            canvas.itemconfig(releaseArc, extent=arcAngle)
            canvas.itemconfig(releaseText, text=f'{release:.2f}')            

    def dialClicked(self, event, stage):
        self.activeDial = stage
        self.clickOrigin = (self.mouse_x, self.mouse_y)

    def mouseReleased(self, event):
        self.activeDial = None

def main():
    # start
    normalizeThread = threading.Thread(target=normalize)
    normalizeThread.start()

    # # update
    # while True:
    #     normalizeThread
    #     for sine in rawAmps:
    #         print(sine.amplitude)
    #     ##print(rawAmps)
    #     time.sleep(1)
    

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
        time.sleep(0.05)


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
        decayThread = threading.Thread(target=fade, args=[sine, note, maxVolume, sustain, decay, "d"])
        decayThread.start()
    elif (stage == "d"):
        pass
        #print("Decay finished")
    
    elif (stage == "r"):
        del rawAmps[sine]
        del normalizedAmps[sine]  
        sine.stream.stop()



def playNote(c: str):

    sine = WaveStreamer(amplitude=0, freq=NOTE_TO_PITCH[c][1])
    sines.append((sine, c))
    attackThread = threading.Thread(target=fade, args=[sine, c, 0, maxVolume, attack, "a"])
    attackThread.start()

    sine.stream.start()

def onKeyPressed(event):
    c = event.char
    if (c not in NOTE_TO_PITCH):
        return
    
    playNote(c)

def onKeyReleased(event):
    for (sine, c) in sines:
        if c == event.keysym:
            currentVolume = sine.amplitude
            releaseThread = threading.Thread(target=fade, args=[sine, c, currentVolume, 0, release, "r"])
            releaseThread.start()
            sines.remove((sine, c))




updateThread = threading.Thread(target=main)
updateThread.start()






root = tk.Tk()
root.title("simplesine")
root.geometry("800x600+100+50")
root.resizable(False, False)

root.bind("<KeyPress>", onKeyPressed)
root.bind("<KeyRelease>", onKeyReleased)

canvas = tk.Canvas(root, width=800,height=600, bg="black")
canvas.pack()


leftx = 50
rightx = 100
offset = 200
inPad = 15
textPad = 25

attackBg = canvas.create_oval(leftx, 49, rightx, 101, fill="white", outline="black", width=1.5, tags="attack_tag")
attackArc = canvas.create_arc(leftx, 50, rightx, 100, fill="lightblue", start= 270, extent=-135)
attackFg = canvas.create_oval(leftx+inPad, 65, (rightx-inPad), 85, fill="black", tags="attack_tag")
attackText = canvas.create_text(leftx+textPad, 108, text=f'{attack:.2f}', fill="white")

decayBg = canvas.create_oval(leftx + offset, 49, rightx + offset, 101, fill="white", outline="black", width=1.5, tags="decay_tag")
decayArc = canvas.create_arc(leftx + offset, 50, rightx + offset, 100, fill="lightblue", start= 270, extent=-135)
decayFg = canvas.create_oval((leftx+inPad) + offset, 65, (rightx-inPad) + offset, 85, fill="black", tags="decay_tag")
decayText = canvas.create_text((leftx+textPad) + offset, 108, text=f'{decay:.2f}', fill="white")

sustainBg = canvas.create_oval(leftx + offset*2, 49, rightx + offset*2, 101, fill="white", outline="black", width=1.5, tags="sustain_tag")
sustainArc = canvas.create_arc(leftx + offset*2, 50, rightx + offset*2, 100, fill="lightblue", start= 270, extent=-135)
sustainFg = canvas.create_oval((leftx+inPad) + offset*2, 65, (rightx-inPad) + offset*2, 85, fill="black", tags="sustain_tag")
sustainText = canvas.create_text((leftx+textPad) + offset*2, 108, text=f'{release:.2f}', fill="white")

releaseBg = canvas.create_oval(leftx + offset*3, 49, rightx+offset*3, 101, fill="white", outline="black", width=1.5, tags="release_tag")
releaseArc = canvas.create_arc(leftx + offset*3, 50, rightx+offset*3, 100, fill="lightblue", start= 270, extent=-135)
releaseFg = canvas.create_oval((leftx+inPad) + offset*3, 65, (rightx-inPad) + offset*3, 85, fill="black", tags="release_tag")
releaseText = canvas.create_text((leftx+textPad) + offset*3, 108, text=f'{release:.2f}', fill="white")

dial = Dials(attackArc)
root.bind("<Motion>", dial.mouseMotion)
root.bind("<ButtonRelease-1>", dial.mouseReleased)
canvas.tag_bind("attack_tag", "<Button-1>", lambda event: dial.dialClicked(event, "attack"))
canvas.tag_bind("decay_tag", "<Button-1>", lambda event: dial.dialClicked(event, "decay"))
canvas.tag_bind("sustain_tag", "<Button-1>", lambda event: dial.dialClicked(event, "sustain"))
canvas.tag_bind("release_tag", "<Button-1>", lambda event: dial.dialClicked(event, "release"))
root.mainloop()
os.system('xset r on')