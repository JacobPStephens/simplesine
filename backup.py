import tkinter as tk
import numpy as np
import sounddevice as sd
import time, threading, os, utils, mido
import matplotlib.pyplot as plt
#from limiter import Limiter


sampleRate = 44100
blocksize = 0 # 0 = default
freq = 440
duration = 5
debugCounter = 0

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

sd.play(wave1, wave2, wave3, wave4)

exit()


lim = Limiter(0.7, 20)
attack = 0.5
decay = 0.25
minDecay = 1e-9
maxDecay = 5
maxVolume = utils.decibelsToAmplitude(-3)
sustain = utils.decibelsToAmplitude(-5)
minSustain = 0
maxSustain = maxVolume
ratioCurve = 1.5

release = 1
minRelease = 1e-9
maxRelease = 8
minAttack = 1e-9
maxAttack = 8

smoothedGain = 0
alphaAttack = 0.6
alphaRelease = 0.01



def midiListener():
    if len(mido.get_input_names()) <= 1:
        return
    portName = mido.get_input_names()[1]
    print(f'{portName=}')
    with mido.open_input(portName) as inport:
        print('listening...')
        for msg in inport:
            onMidiAction(msg)

class Note:
    def __init__(self, freq):
        self.start = time.time()
        self.freq = freq
        self.phase = 0
        self.released = False
        self.releaseStart = None
        self.volumeAtReleaseStart = 0
        self.dead = False
        self.prevAmplitude = 0
        self.amp = 0

    def getAmp(self, startVolume, endVolume, ratio):
        self.amp = startVolume + ((endVolume - startVolume) * ratio**ratioCurve)
        return self.amp

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
                self.amp = sustain
                return sustain
        # release phase
        else:
            #print(f'in release: {self.amp=}')
            if not self.releaseStart:
                self.releaseStart = lifetime
                self.volumeAtReleaseStart = self.amp
                #print(f'set volume at release start to {self.volumeAtReleaseStart}')

            ratio = (lifetime - self.releaseStart) / release
            if ratio > 1:
                self.dead = True
                #print("note dead", lifetime)
                return 0
            

            # global debugCounter
            # #print("release", lifetime)
            # if debugCounter < 10:
            #     print(f'{ratio=}')
            #     debugCounter += 1
            # else:
            #     exit()
            return self.getAmp(self.volumeAtReleaseStart, 0, ratio)

    def generate(self, frames, startTimeOfBlock):

        timesBySample = startTimeOfBlock + np.arange(frames) / sampleRate #startTimeOfBlock + np.arange(frames) / sampleRate


        amplitudes = np.array([self.envelope(t) for t in timesBySample])

        # smooth amplitudes between each bus of frames
        amplitudes = np.linspace(self.prevAmplitude, amplitudes[-1], frames)
        self.prevAmplitude = amplitudes[-1]

        phaseIncrement = 2 * np.pi * self.freq / sampleRate # radians per sample travelled
        phases = np.arange(frames) * phaseIncrement + self.phase
        signal = amplitudes * np.sin(phases)


        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)
        print(self.phase)
        

        return signal



def audioCallback(outdata, frames, time_info, status):
    if status: 
        print(f'{status=}')
    
    if (stream.cpu_load > 0.2):
        print(f'cpu {stream.cpu_load}')
    signal = np.zeros(frames, dtype=np.float32)
    with lock:
        startTime = time.time()
        for note in activeNotes[:]:
            if note.dead:
                activeNotes.remove(note)
                continue
            signal = signal + note.generate(frames, startTime)
            #signal = lim.process(signal)
            #signal = normalize(signal, note.generate(frames, startTime)) 

    peak = np.max(np.abs(signal)) + 1e-10
    #print(f'rawPeak={peak}')
    if peak > 1:
        targetGain = 1 / peak
    else:
        targetGain = 1     

    global smoothedGain

    if targetGain < smoothedGain:
        smoothedGain = smoothedGain * (1 - alphaAttack) + targetGain * alphaAttack 
    else:
        smoothedGain = smoothedGain * (1 - alphaRelease) + targetGain * alphaRelease 

    #print(f'{targetGain=}')
    signal *= smoothedGain * 0.5
    peak = np.max(np.abs(signal))

    
    if peak > 1:
        print(f"clip {peak}")
        #np.clip(signal, -1.0, 1.0)
    #print(f'{peak=}')

    # peak = np.max(np.abs(signal))
    # if peak > 1:
    #     signal = signal / (peak)
    #signal = np.tanh(signal) 

    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)


# buffer = (wave1 + wave2 + wave3 + wave4)
# sd.play(buffer * 0.1)
#plt.ion()
activeNotes = []
signals = []
lock = threading.Lock()

blackIDs = [1, 3, 6, 8 ,10, 13, 15, 18, 20, 22]
whiteIDs = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24]

LOWEST_NOTE = 48

def transposeKeys(amount: int):
    global LOWEST_NOTE
    LOWEST_NOTE += amount
    print(f'New {LOWEST_NOTE=}')

def highlightNote(noteID, msgType):
    
    localID = noteID - LOWEST_NOTE # where note 48 is the lowest element in current 8ve
    if not (0 <= localID <= 25):
        return

    #print(f'{localID=}')
    
    if msgType == "note_on":
        canvas.itemconfig(keysGUI[localID], fill="white")

    elif msgType == "note_off": 

        if localID in whiteIDs:
            canvas.itemconfig(keysGUI[localID], fill=secondaryBlue)

        elif localID in blackIDs:
            canvas.itemconfig(keysGUI[localID], fill=primaryBlue)


    #print("highlighting note s", noteID)
    

def onMidiAction(msg):

    if not msg.note:
        return
    
    # cap at c8
    if msg.note > 108:
        return
    
    with lock: 
        freq = utils.NOTE_TO_FREQ[msg.note]
        if msg.type == "note_on":
            activeNotes.append(Note(freq))
            

        elif msg.type == "note_off":
            for note in activeNotes:
                if note.freq == freq and not note.released:
                    note.released = True

        highlightNote(msg.note, msg.type)


# def onKeyPressed(event):
#     if event.char not in NOTE_TO_PITCH:
#         return

#     with lock:
#         freq = NOTE_TO_PITCH[event.char][1]
#         activeNotes.append(Note(freq))

def onKeyPressed(event):
    if event.char == ")":        
        transposeKeys(1)
    elif event.char == "(":
        transposeKeys(-1)
    elif event.char == "+":
        transposeKeys(12)
    elif event.char == "-":
        transposeKeys(-12)

    if event.char.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
        return
    
    localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.char.lower()]
    globalNote = localNote + LOWEST_NOTE
    if globalNote > 88:
        return
    
    freq = utils.NOTE_TO_FREQ[globalNote]
    with lock:
        activeNotes.append(Note(freq))
        highlightNote(globalNote, "note_on")


def onKeyReleased(event):
    if event.keysym.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
        return
    
    localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.keysym.lower()]
    globalNote = localNote + LOWEST_NOTE
    freq = utils.NOTE_TO_FREQ[globalNote]

    with lock:
        for note in activeNotes:
            if note.freq == freq and not note.released:
                note.released = True
                highlightNote(globalNote, "note_off")

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
        arcAngle = ((difference + 50) / (100 + 1e-9)) *-360

        canvas.itemconfig(self.activeDial.arc, extent=arcAngle)
        canvas.itemconfig(self.activeDial.text, text=f'{self.activeDial.name:.2f}s')


        if self.activeDial == "attack":
            attack = minAttack + (maxAttack - minAttack) * (abs(arcAngle) / 360)**2 # smooths out dial 
            canvas.itemconfig(attackArc, extent=arcAngle)
            canvas.itemconfig(attackText, text=f'{attack:.2f}s')

        elif self.activeDial == "decay":
            decay = minDecay + (maxDecay - minDecay) * (abs(arcAngle) / 360)**2
            canvas.itemconfig(decayArc, extent=arcAngle)
            canvas.itemconfig(decayText, text=f'{decay:.2f}s') 

        elif self.activeDial == "sustain":
            sustain = minSustain + (maxSustain - minSustain) * (abs(arcAngle) / 360)**2
            canvas.itemconfig(sustainArc, extent=arcAngle)
            canvas.itemconfig(sustainText, text=f'{utils.amplitudeToDecibels(sustain):.2f}dB')  

        elif self.activeDial == "release":
            release = minRelease + (maxRelease - minRelease) * (abs(arcAngle) / 360)**2
            canvas.itemconfig(releaseArc, extent=arcAngle)
            canvas.itemconfig(releaseText, text=f'{release:.2f}s')            

    def dialClicked(self, event, stage):
        self.activeDial = stage
        self.clickOrigin = (self.mouse_x, self.mouse_y)

    def mouseReleased(self, event):
        self.activeDial = None



root = tk.Tk()
root.title("simplesine")
root.geometry("800x405+100+50")
root.resizable(False, False)

root.bind("<KeyPress>", onKeyPressed)
root.bind("<KeyRelease>", onKeyReleased)

canvas = tk.Canvas(root, width=800,height=405, bg="#2B2B2B")
canvas.pack()


primaryBlue = "#50ACC0"
secondaryBlue = "#1E393F"
primaryGray = "#2B2B2B"
secondaryGray = "#1E1E1E"


borderTop = canvas.create_rectangle(0, 0, 800, 10, fill=primaryBlue)
borderBot = canvas.create_rectangle(0, 395, 800, 405, fill=primaryBlue)
borderLeft = canvas.create_rectangle(0, 10, 10, 395, fill=primaryBlue)
borderRight = canvas.create_rectangle(790, 10, 800, 395, fill=primaryBlue)

bgMid = canvas.create_rectangle(210, 10, 590, 395, fill=secondaryGray, outline=None)

effectsTxt = canvas.create_text(690, 30, text="effects", justify='center', font=("Terminal", 16, 'bold'), fill=secondaryGray)
modulationsTxt = canvas.create_text(110, 30, text="modulations", justify='center', font=("Terminal", 16, 'bold'), fill=secondaryGray)
centerTitle = canvas.create_text(400, 40, text="simplesine", justify='center', font=("Terminal", 30, 'bold'), fill=primaryBlue)


BOTTOM_NOTE = 48
whiteKeys = []
leftx = 10
whiteKeyWidth = 52.0 # (800 - 10 - 10) / 15 (#keys)
whiteKeyHeight = 80

heightOffset = 30
blackKeyWidth = 20
blackKeyHeight = 50
keysGUI = []
keyTexts = []

for i in range(29):
    if i in [5, 13, 19, 27]:
        keysGUI.append(0)
        keyTexts.append(0)
    elif (i % 2 == 0):
        tmp = canvas.create_rectangle(leftx, 395-whiteKeyHeight, leftx+whiteKeyWidth, 395, fill=secondaryBlue, outline="white")
        keyTexts.append(canvas.create_text(leftx+(whiteKeyWidth/2), 395-(whiteKeyHeight * 1 / 4), text=utils.keyboardKeys[i], font=("Terminal", 9), fill="#CCCCCC"))

        keysGUI.append(tmp)
        leftx += whiteKeyWidth
    else:
        tmp = canvas.create_rectangle(leftx-(blackKeyWidth/2), 395-blackKeyHeight-heightOffset, leftx+blackKeyWidth-(blackKeyWidth/2), 395-heightOffset,fill=primaryBlue,outline="white")
        keyTexts.append(canvas.create_text(leftx, 395-(blackKeyHeight), text=utils.keyboardKeys[i], font=("Terminal", 9), fill='white'))
        keysGUI.append(tmp)

# lift all black keys to front of canvas
for i in range(len(keysGUI)):
    if keysGUI[i] and (i % 2 == 1):
        canvas.lift(keysGUI[i])
        canvas.lift(keyTexts[i])
        

# remove dummy 0s from keyGUI list
numRemoved = 0
for i in [5, 13, 19, 27]:
    keysGUI.pop(i-numRemoved)
    numRemoved += 1


    # # white keys
    # if i in [0,2,4,5,7,9,11,12,14,16,17,19,21,23,24]:
    #     leftx += whiteKeyWidth

    # # black keys                       
    # else:
    



# for i in range(15):
#     whiteKeys.append())
#     leftx += whiteKeyWidth

# blackKeys = []
# leftx = 10 + whiteKeyWidth
# blackKeyWidth = 20
# keyHeight = 50

# for i in range(13):
#     if i not in [2, 6, 9]:
#         blackKeys.append()
#     leftx += whiteKeyWidth


panelHeight = 305 # total height - 2 * border - keysHeight
leftPanelLines = []
rightPanelLines = []
panelLineHeight = 3
for i in range(1,4):
    y = (panelHeight/4*i) + 10
    leftPanelLines.append(canvas.create_rectangle(10, y, 210, y+panelLineHeight, fill=secondaryGray))
    rightPanelLines.append(canvas.create_rectangle(590, y, 790, y+panelLineHeight, fill=secondaryGray))


def makeGUIStringPerStage(stage: str) -> str:
    stageCap = stage[0].upper() + stage[1:]
    return f"startExtent = (({stage}-min{stageCap}) / (max{stageCap}-min{stageCap}))**(1/2) * 360\n" \
           f"{stage}Arc = canvas.create_arc({stage}Center-(dialWidth/2), yCenter-(dialHeight/2), {stage}Center+(dialWidth/2), yCenter+(dialHeight/2), fill=primaryBlue, start=270, extent=-startExtent, tags='attack_tag')\n" \
           f"{stage}Text = canvas.create_text({stage}Center, yCenter+(dialWidth/2)+textPad, text={f'{stage}'}, fill='white')"


#attackText = canvas.create_text(attackCenter, yCenter+(dialWidth/2)+textPad, text=f'{attack:.2f}s', fill="white")


a = "this is a " \
"multiple line string"
#print(generateStartExtentEquation("attack"))


leftx = 50
rightx = 100
offset = 200
inPad = 15
textPad = 10

dialHeight = 60
dialWidth = 60

yCenter = 260
attackCenter = 260
decayCenter = 353.33
sustainCenter = 446.66
releaseCenter = 540
#attackBg = canvas.create_oval(leftx, 49, rightx, 101, fill="white", outline="black", width=1.5, tags="attack_tag")
attackBg = canvas.create_oval(attackCenter-(dialWidth/2), yCenter-(dialHeight/2), attackCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=secondaryBlue, outline="black", width=1.5, tags="attack_tag")
# ^^ 20 pad from top of keys .. 20 pad from left of center dark gray box
#startExtent = ((attack-minAttack) / (maxAttack-minAttack))**(1/2) * 360
#startExtent = 0
#exec(generateStartExtentEquation("attack"))
exec(makeGUIStringPerStage("attack"))
#attackArc = canvas.create_arc(attackCenter-(dialWidth/2), yCenter-(dialHeight/2), attackCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=primaryBlue, start=270, extent=-startExtent, tags="attack_tag")
#attackText = canvas.create_text(attackCenter, yCenter+(dialWidth/2)+textPad, text=f'{attack:.2f}s', fill="white")

#startExtent = ((decay-minDeacy) / (maxAttack-minAttack))**(1/2) * 360
#exec(generateStartExtentEquation("attack"))
decayBg = canvas.create_oval(decayCenter-(dialWidth/2), yCenter-(dialHeight/2), decayCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=secondaryBlue, outline="black", width=1.5, tags="decay_tag")
decayArc = canvas.create_arc(decayCenter-(dialWidth/2), yCenter-(dialHeight/2), decayCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=primaryBlue, start= 270, extent=-359, tags="decay_tag")

#decayFg = canvas.create_oval((leftx+inPad) + offset, 65, (rightx-inPad) + offset, 85, fill="black", tags="decay_tag")
decayText = canvas.create_text(decayCenter, yCenter+(dialHeight/2)+textPad, text=f'{decay:.2f}s', fill="white")
#decayDesc = canvas.create_text((leftx+textPad) + offset, 120, text=f'peak to sustain', fill="white", font=("Arial", 10))

#sustainBg = canvas.create_oval(leftx + offset*2, 49, rightx + offset*2, 101, fill="white", outline="black", width=1.5, tags="sustain_tag")
sustainBg = canvas.create_oval(sustainCenter-(dialWidth/2), yCenter-(dialHeight/2), sustainCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=secondaryBlue, outline="black", width=1.5, tags="sustain_tag")
sustainArc = canvas.create_arc(sustainCenter-(dialWidth/2), yCenter-(dialHeight/2), sustainCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=primaryBlue, start= 270, extent=-359, tags="sustain_tag")

#sustainFg = canvas.create_oval((leftx+inPad) + offset*2, 65, (rightx-inPad) + offset*2, 85, fill="black", tags="sustain_tag")
sustainText = canvas.create_text(sustainCenter, yCenter+(dialWidth/2)+textPad, text=f'{release:.2f}dB', fill="white")
#sustainDesc = canvas.create_text((leftx+textPad) + offset*2, 120, text=f'sustain volume', fill="white", font=("Arial", 10))

 
#releaseBg = canvas.create_oval(570, 290-dialHeight, 570-dialWidth, 290, fill=secondaryBlue, outline="black", width=1.5, tags="attack_tag")\attackBg = canvas.create_oval(attackCenter-(dialWidth/2), attackCenter-(dialHeight/2), attackCenter+(dialWidth/2), attackCenter+(dialHeight/2), fill=secondaryBlue, outline="black", width=1.5, tags="attack_tag")
releaseBg = canvas.create_oval(releaseCenter-(dialWidth/2), yCenter-(dialHeight/2), releaseCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=secondaryBlue, outline="black", width=1.5, tags="release_tag")
releaseArc = canvas.create_arc(releaseCenter-(dialWidth/2), yCenter-(dialHeight/2), releaseCenter+(dialWidth/2), yCenter+(dialHeight/2), fill=primaryBlue, start= 270, extent=-359, tags="release_tag")

#
#releaseBg = canvas.create_oval(leftx + offset*3, 49, rightx+offset*3, 101, fill="white", outline="black", width=1.5, tags="release_tag")
#releaseFg = canvas.create_oval((leftx+inPad) + offset*3, 65, (rightx-inPad) + offset*3, 85, fill="black", tags="release_tag")
releaseText = canvas.create_text(releaseCenter, yCenter+(dialWidth/2)+textPad, text=f'{release:.2f}s', fill="white")
#releaseDesc = canvas.create_text((leftx+textPad) + offset*3, 120, text=f'time to silence', fill="white", font=("Arial", 10))

stream = sd.OutputStream(samplerate=sampleRate, channels=2, callback=audioCallback, blocksize=blocksize)
stream.start()

midiThread = threading.Thread(target=midiListener)
midiThread.start()

dial = Dials(attackArc)
root.bind("<Motion>", dial.mouseMotion)
root.bind("<ButtonRelease-1>", dial.mouseReleased)

''' can be done in a for loop '''
canvas.tag_bind("attack_tag", "<Button-1>", lambda event: dial.dialClicked(event, "attack"))
canvas.tag_bind("decay_tag", "<Button-1>", lambda event: dial.dialClicked(event, "decay"))
canvas.tag_bind("sustain_tag", "<Button-1>", lambda event: dial.dialClicked(event, "sustain"))
canvas.tag_bind("release_tag", "<Button-1>", lambda event: dial.dialClicked(event, "release"))
root.mainloop()
os.system('xset r on')
#stream.stop()