import tkinter as tk
import numpy as np
import sounddevice as sd
import time, threading, os, utils
import matplotlib.pyplot as plt
from limiter import Limiter


sampleRate = 44100
blocksize = 0 # default
freq = 440
duration = 5
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




buffer = np.arange(sampleRate * duration)
wave1 = np.sin(2 * np.pi * np.arange(sampleRate * duration) * (261.63 / sampleRate)).reshape(-1, 1)
wave2 = np.sin(2 * np.pi * np.arange(sampleRate * duration) * (329 / sampleRate)).reshape(-1, 1)
wave3 = np.sin(2 * np.pi * np.arange(sampleRate * duration) * (392 / sampleRate)).reshape(-1, 1)
wave4 = np.sin(2 * np.pi * np.arange(sampleRate * duration) * (493 / sampleRate)).reshape(-1, 1)


lim = Limiter(0.9, 20)
attack = 1
decay = 0.25
minDecay = 1e-9
maxDecay = 5
maxVolume = 2 #utils.decibelsToAmplitude(-2)
sustain = utils.decibelsToAmplitude(-5)
minSustain = 0
maxSustain = maxVolume
release = 2
minRelease = 1e-9
maxRelease = 8
minAttack = 1e-9
maxAttack = 8

class Note:
    def __init__(self, freq):
        self.start = time.time()
        self.freq = freq
        self.phase = 0
        self.released = False
        self.releaseStart = None
        self.dead = False
        self.prevAmplitude = 0

    def getAmp(self, startVolume, endVolume, ratio):
        return startVolume + ((endVolume - startVolume) * ratio)

    def envelope(self, t) -> float:
        assert all([attack, decay, release]) # remove later
        ''' Returns correct amplitude of note based on time in envelope '''
        lifetime = t - self.start
        if not self.released:
            # attack phase
            if lifetime < attack:
                #print("attack", lifetime)
                ratio = lifetime / attack
                return self.getAmp(0, maxVolume, ratio)
            # decay phase
            elif lifetime < (attack + decay):
                #print("decay", lifetime)
                ratio = (lifetime - attack) / decay
                return self.getAmp(maxVolume, sustain, ratio)
            # sustain phase
            else:
                #print("sustain", lifetime)
                return sustain
        # release phase
        else:
            if not self.releaseStart:
                self.releaseStart = lifetime

            ratio = (lifetime - self.releaseStart) / release
            if ratio > 1:
                self.dead = True
                #print("note dead", lifetime)
                return 0
            
            #print("release", lifetime)
            return self.getAmp(sustain, 0, ratio)

    def generate(self, frames, startTimeOfBlock):

        timesBySample = startTimeOfBlock + np.arange(frames) / sampleRate #startTimeOfBlock + np.arange(frames) / sampleRate

        amplitudes = np.array([self.envelope(t) for t in timesBySample])
        amplitudes = np.linspace(self.prevAmplitude, amplitudes[-1], frames)
        self.prevAmplitude = amplitudes[-1]

        phaseIncrement = 2 * np.pi * self.freq / sampleRate # radians per sample travelled
        phases = np.arange(frames) * phaseIncrement + self.phase
        signal = amplitudes * np.sin(phases)

        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)

        # t = (np.arange(frames) + self.phase) / sampleRate
        # signal = amplitudes * np.sin(2 * np.pi * self.freq * t)
    
        # modded by total number of samples in one cycle. 
        # Unit of phase here is samples (not radians)
        # self.phase = (self.phase + frames) % (1/self.freq * sampleRate)

        return signal



def normalize(signal):
    maxPoint = np.max(np.abs(signal))
    if maxPoint > 1:
        signal = signal / maxPoint
    return signal

def audioCallback(outdata, frames, time_info, status):
    if status: 
        print(f'{status=}')
    #print(stream.cpu_load)
    signal = np.zeros(frames, dtype=np.float32)
    with lock:
        startTime = time.time()
        for note in activeNotes:
            if note.dead:
                activeNotes.remove(note)
            signal += note.generate(frames, startTime)

    #signal = lim.process(signal)
    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)


# buffer = (wave1 + wave2 + wave3 + wave4)
# sd.play(buffer * 0.1)
#plt.ion()
activeNotes = []
lock = threading.Lock()

def onKeyPressed(event):
    if event.char not in NOTE_TO_PITCH:
        return

    with lock:
        freq = NOTE_TO_PITCH[event.char][1]
        activeNotes.append(Note(freq))


def onKeyReleased(event):
    if event.keysym not in NOTE_TO_PITCH:
        return
    freq = NOTE_TO_PITCH[event.keysym][1]
    with lock:
        for note in activeNotes:
            if note.freq == freq and not note.released:
                note.released = True

    #plt.show(block=True)

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
        arcAngle = ((difference + 50) / (100 + 1e-9)) * -360

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

leftx = 50
rightx = 100
offset = 200
inPad = 15
textPad = 25

root = tk.Tk()
root.title("simplesine")
root.geometry("800x600+100+50")
root.resizable(False, False)

root.bind("<KeyPress>", onKeyPressed)
root.bind("<KeyRelease>", onKeyReleased)

canvas = tk.Canvas(root, width=800,height=600, bg="black")
canvas.pack()

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

stream = sd.OutputStream(samplerate=sampleRate, channels=2, callback=audioCallback, blocksize=blocksize)
stream.start()

dial = Dials(attackArc)
root.bind("<Motion>", dial.mouseMotion)
root.bind("<ButtonRelease-1>", dial.mouseReleased)
canvas.tag_bind("attack_tag", "<Button-1>", lambda event: dial.dialClicked(event, "attack"))
canvas.tag_bind("decay_tag", "<Button-1>", lambda event: dial.dialClicked(event, "decay"))
canvas.tag_bind("sustain_tag", "<Button-1>", lambda event: dial.dialClicked(event, "sustain"))
canvas.tag_bind("release_tag", "<Button-1>", lambda event: dial.dialClicked(event, "release"))
root.mainloop()
os.system('xset r on')
#stream.stop()