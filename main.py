import tkinter as tk
import numpy as np
import sounddevice as sd
import threading, mido, utils, params, time, os


# apparent global values
attack = params.defaultAttack
decay = params.defaultDecay
sustain = params.defaultSustain
release = params.defaultRelease
maxVolume = params.defaultMaxVolume
lowestNote = params.defaultLowestNote
dialValues = {
    'attack': {
        'curr': params.defaultAttack,
        'min': params.minAttack,
        'max': params.maxAttack,
        'center': 260
    },
    'decay': {
        'curr': params.defaultDecay,
        'min': params.minDecay,
        'max': params.maxDecay,
        'center': 353.33
    },
    'sustain': {
        'curr': params.defaultSustain,
        'min': params.minSustain,
        'max': params.maxSustain,
        'center': 446.66
    },
    'release': {
        'curr': params.defaultRelease,
        'min': params.minRelease,
        'max': params.maxRelease,
        'center': 540
    }
}


#pitch = b

# variables that are changing live should be globals in main.
# otherwise, put to params that get changed eveyr start

def main():
    global lock, activeNotes, stream, inputObj

    os.system('xset r off')
    
    buildGUI()

    activeNotes = []
    lock = threading.Lock()

    # build widgets 
    widgets = {}
    # ADSR knobs
    for name in ['attack', 'decay', 'sustain', 'release']:
        widgets[name] = Dial(name)

    # bind keyboard input to callback function
    inputObj = UserInput(widgets)
    root.bind("<KeyPress>", inputObj.onKeyPressed)
    root.bind("<KeyRelease>", inputObj.onKeyReleased)
    root.bind("<Motion>", inputObj.mouseMotion)
    root.bind("<ButtonRelease-1>", inputObj.mouseReleased)

    # listen for midi input
    midiThread = threading.Thread(target=inputObj.midiListener)
    midiThread.start()
    # start audio stream
    stream = sd.OutputStream(samplerate=params.samplerate, channels=2, callback=audioCallback, blocksize=params.blocksize)
    stream.start()



    root.mainloop()
    os.system('xset r on')

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
            #signal = normalize(signal, note.generate(frames, startTime)) 

    peak = np.max(np.abs(signal)) + 1e-10
    #print(f'rawPeak={peak}')
    if peak > 1:
        targetGain = 1 / peak
    else:
        targetGain = 1     

    if targetGain < params.smoothedGain:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaAttack) + targetGain * params.alphaAttack 
    else:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaRelease) + targetGain * params.alphaRelease 

    #print(f'{targetGain=}')
    signal *= params.smoothedGain * 0.5
    peak = np.max(np.abs(signal))

    
    if peak > 1:
        print(f"clip {peak}")


    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)

def buildGUI():
    global root, canvas, keysGUI
    # build root
    root = tk.Tk()    
    root.geometry("800x405+100+50")
    root.resizable(False, False)
    root.title("simplesine")

    canvas = tk.Canvas(root, width=800,height=405, bg="#2B2B2B")
    
    # build 4 sides of window border
    canvas.create_rectangle(0, 0, 800, 10, fill=params.primaryToneLight)
    canvas.create_rectangle(0, 395, 800, 405, fill=params.primaryToneLight)
    canvas.create_rectangle(0, 10, 10, 395, fill=params.primaryToneLight)
    canvas.create_rectangle(790, 10, 800, 395, fill=params.primaryToneLight)

    # build panels
    bgMid = canvas.create_rectangle(210, 10, 590, 395, fill=params.secondaryToneDark, outline=None)
    effectsTxt = canvas.create_text(690, 30, text="effects", justify='center', font=("Terminal", 16, 'bold'), fill=params.secondaryToneDark)
    modulationsTxt = canvas.create_text(110, 30, text="modulations", justify='center', font=("Terminal", 16, 'bold'), fill=params.secondaryToneDark)
    centerTitle = canvas.create_text(400, 40, text="simplesine", justify='center', font=("Terminal", 30, 'bold'), fill=params.primaryToneLight)
    
    panelHeight = 305 # total height - 2 * border - keysHeight
    leftPanelLines = []
    rightPanelLines = []
    panelLineHeight = 3
    for i in range(1,4):
        y = (panelHeight/4*i) + 10
        leftPanelLines.append(canvas.create_rectangle(10, y, 210, y+panelLineHeight, fill=params.secondaryToneDark))
        rightPanelLines.append(canvas.create_rectangle(590, y, 790, y+panelLineHeight, fill=params.secondaryToneDark))

    # build piano keys
    leftx = 10
    whiteKeyWidth = 52.0 # (800 - 10 - 10) / 15 (#keys)
    whiteKeyHeight = 80
    heightOffset = 30
    blackKeyWidth = 20
    blackKeyHeight = 50
    keyTexts = []
    keysGUI = []

    for i in range(29):
        if i in [5, 13, 19, 27]:
            keysGUI.append(0)
            keyTexts.append(0)
        elif (i % 2 == 0):
            tmp = canvas.create_rectangle(leftx, 395-whiteKeyHeight, leftx+whiteKeyWidth, 395, fill=params.primaryToneDark, outline="white")
            keyTexts.append(canvas.create_text(leftx+(whiteKeyWidth/2), 395-(whiteKeyHeight * 1 / 4), text=utils.keyboardKeys[i], font=("Terminal", 9), fill="#CCCCCC"))

            keysGUI.append(tmp)
            leftx += whiteKeyWidth
        else:
            tmp = canvas.create_rectangle(leftx-(blackKeyWidth/2), 395-blackKeyHeight-heightOffset, leftx+blackKeyWidth-(blackKeyWidth/2), 395-heightOffset,fill=params.primaryToneLight,outline="white")
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

    canvas.pack()

class Dial:
    def __init__(self, name):
        self.name = name
        dialWidth = params.dialWidth
        dialHeight = params.dialHeight
        dialCenter_y = params.dialCenter_y
        dialCenters_x = params.dialCenters_x
        textPadding = params.textPadding
        startExtent = self.getStartExtent(self.name)
        tagName = f'{self.name}_tag'
        self.bg = canvas.create_oval(dialCenters_x[self.name]-(dialWidth/2), dialCenter_y-(dialHeight/2), dialCenters_x[self.name]+(dialWidth/2), dialCenter_y+(dialHeight/2), fill=params.primaryToneDark, outline="black", width=1.5, tags=tagName)
        self.arc = canvas.create_arc(dialCenters_x[self.name]-(dialWidth/2), dialCenter_y-(dialHeight/2), dialCenters_x[self.name]+(dialWidth/2), dialCenter_y+(dialHeight/2), fill=params.primaryToneLight, start= 270, extent=startExtent, tags=tagName)
        canvas.tag_bind(tagName, "<Button-1>", lambda event: inputObj.mouseClicked(event, self.name))
        #allTags.append(tagName)
        if self.name != "sustain":
            self.text = canvas.create_text(dialCenters_x[self.name], dialCenter_y+(dialHeight/2)+textPadding, text=f'{dialValues[self.name]['curr']:.2f}s', fill="white")
        else:
            self.text = canvas.create_text(dialCenters_x[self.name], dialCenter_y+(dialHeight/2)+textPadding, text=f'{utils.amplitudeToDecibels(dialValues[self.name]['curr']):.2f}dB', fill="white")
        
    def update(self, clickPoint, mousePoint):
        # calculate dial angle using user's mouse location
        verticalDiff = clickPoint[1] - mousePoint[1]
        clampedDiff = min(50, max(-50, verticalDiff))
        dialAngle = ((clampedDiff + 50) / (100 + 1e-9)) *-360
        # update dial GUI angle
        canvas.itemconfig(self.arc, extent=dialAngle)
        # calculate current value of ADSR dial given GUI angle
        minDialValue = dialValues[self.name]['min']
        maxDialValue = dialValues[self.name]['max']
        dialValues[self.name]['curr'] = minDialValue + (maxDialValue - minDialValue) * abs(dialAngle/360)**2
        # update text to match value
        if self.name != "sustain":
            canvas.itemconfig(self.text, text=f'{dialValues[self.name]['curr']:.2f}s')
        else:
            canvas.itemconfig(self.text, text=f'{utils.amplitudeToDecibels(dialValues[self.name]['curr']):.2f}dB')
    
    def getStartExtent(self, name):
        env = dialValues[name]
        return -360 * ((env['curr']-env['min']) / (env['max']-env['min']))**(1/2)


class Slider:
    def __init__(self):
        pass

    def update(self, clickPoint, mousePoint):
        pass
        # called when mouse moves and you are active
        # update variables like maxVolume


class UserInput():
    def __init__(self, widgets):
        self.mousePoint: tuple[int, int] = None
        self.clickPoint: tuple[int, int] = None
        self.widgets = widgets
        self.activeWidget = None

    def mouseClicked(self, event, stage):
        self.activeWidget = self.widgets[stage]
        self.clickPoint = self.mousePoint

    def mouseReleased(self, event):
        self.activeWidget = None

    def mouseMotion(self, event):
        self.mousePoint = (event.x, event.y)
        if self.activeWidget:
            self.widgets[self.activeWidget.name].update(self.clickPoint, self.mousePoint)
    
    def onKeyPressed(self, event):
        charToTranposeAmount = {
            ")": 1,
            "(": -1,
            "+": 12,
            "-": -12
        }
        if event.char in charToTranposeAmount:
            amnt = charToTranposeAmount[event.char]
            utils.transpose(amnt)
        if event.char.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
            return
        localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.char.lower()]
        globalNote = localNote + lowestNote
        if globalNote > params.noteCeiling:
            return
        notePlayed(globalNote)

    def onKeyReleased(self, event):
        if event.keysym.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
            return
        localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.keysym.lower()]
        globalNote = localNote + lowestNote
        noteReleased(globalNote)

    def midiListener(self):
        if len(mido.get_input_names()) <= 1:
            return
        portName = mido.get_input_names()[1]
        print(f'{portName=}')
        with mido.open_input(portName) as inport:
            print('listening...')
            for msg in inport:
                self.onMidiAction(msg)

    def onMidiAction(self,msg):
        if not msg.note or msg.note > 108:
            return
        
        # maybe add lock here
        if msg.type == "note_on":
            notePlayed(msg.note)
            
        elif msg.type == "note_off":
            noteReleased(msg.note)

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
        self.amp = startVolume + ((endVolume - startVolume) * ratio**params.ratioCurve)
        return self.amp

    def envelope(self, t) -> float:
        #assert all([attack, decay, release]) # remove later
        attack = dialValues['attack']['curr']
        decay = dialValues['decay']['curr']
        sustain = dialValues['sustain']['curr']
        release = dialValues['release']['curr']

        ''' Returns correct amplitude of note based on time in envelope '''
        lifetime = t - self.start
        if not self.released:
            # attack phase
            if lifetime < attack:
                #print("attack", lifetime)
                ratio = lifetime / attack
                return self.getAmp(0, params.defaultMaxVolume, ratio)
            # decay phase
            elif lifetime < (attack + decay):
                #print("decay", lifetime)
                ratio = (lifetime - attack) / decay
                return self.getAmp(params.defaultMaxVolume, sustain, ratio)
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
            

            return self.getAmp(self.volumeAtReleaseStart, 0, ratio)

    def generate(self, frames, startTimeOfBlock):

        timesBySample = startTimeOfBlock + np.arange(frames) / params.samplerate #startTimeOfBlock + np.arange(frames) / sampleRate


        amplitudes = np.array([self.envelope(t) for t in timesBySample])

        # smooth amplitudes between each bus of frames
        amplitudes = np.linspace(self.prevAmplitude, amplitudes[-1], frames)
        self.prevAmplitude = amplitudes[-1]

        phaseIncrement = 2 * np.pi * self.freq / params.samplerate # radians per sample travelled
        phases = np.arange(frames) * phaseIncrement + self.phase
        signal = amplitudes * np.sin(phases)

        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)

        return signal

# NOTES PLAYED/RELEASED
def notePlayed(globalNoteID):
    with lock:
        freq = utils.NOTE_TO_FREQ[globalNoteID]
        activeNotes.append(Note(freq))
        highlightNote(globalNoteID, "note_on")

def noteReleased(globalNoteID):
    with lock:
        freq = utils.NOTE_TO_FREQ[globalNoteID]
        for note in activeNotes:
            if note.freq == freq and not note.released:
                note.released = True
        highlightNote(globalNoteID, "note_off")

def highlightNote(noteID, msgType):
    
        localID = noteID - lowestNote # where note 48 is the lowest element in current 8ve
        if not (0 <= localID <= 25):
            return

        #print(f'{localID=}')
        
        if msgType == "note_on":
            canvas.itemconfig(keysGUI[localID], fill="white")

        elif msgType == "note_off": 

            if localID in utils.whiteIDs:
                canvas.itemconfig(keysGUI[localID], fill=params.primaryToneDark)

            elif localID in utils.blackIDs:
                canvas.itemconfig(keysGUI[localID], fill=params.primaryToneLight)


main()