import tkinter as tk
import numpy as np
import sounddevice as sd
import threading, mido, utils, params, time, os


from classes import (
    PanelComponent,
    Effect,
    Distortion,
    Delay,
    Compressor,
    Filter,
    Modulation,
    Oscillator,
    Envelope,
    Dial,
    Dropdown
)

def main():
    global lock, stream, state
    os.system('xset r off')
    state = State()

    buildGUI()
    lock = threading.Lock()
    
    for name in ['attack', 'decay', 'sustain', 'release']:
        dialType = state.dialValues[name]
        label = ""
        if name == "sustain":
            units = ""
        else:
            units = "s"
        state.widgets[name] = Dial(dialType['centerX'], dialType['centerY'], params.dialWidth, dialType['min'], dialType['max'], name, label="", canvas=canvas, state=state, units=units, isADSR=True, ratioRamp=2)


    state.widgets['volume'] = Slider('volume')
    state.widgets['frequency'] = Slider('frequency')

    # bind keyboard input to callback function
    
    root.bind("<KeyPress>", state.inputObj.onKeyPressed)
    root.bind("<KeyRelease>", state.inputObj.onKeyReleased)
    root.bind("<Motion>", state.inputObj.mouseMotion)
    root.bind("<ButtonRelease-1>", state.inputObj.mouseReleased)
    root.bind("<Button-3>", state.inputObj.mouseSecondaryPressed)

    root.after(500, draw)
    # listen for midi input
    midiThread = threading.Thread(target=state.inputObj.midiListener)
    midiThread.start()
    # start audio stream
    stream = sd.OutputStream(
    samplerate=params.samplerate,
    channels=2, 
    callback=audioCallback, 
    blocksize=params.blocksize
    )
    stream.start()

    root.mainloop()
    os.system('xset r on')

# global synth settings -- maybe don't need adsr here
attack = params.defaultAttack
decay = params.defaultDecay
sustain = params.defaultSustain
release = params.defaultRelease
peakVolume = params.peakVolume
volume = params.volume
lowestNote = params.defaultLowestNote


class State:
    def __init__(self):
        self.waveType = "sine"
        self.effectObjs = [None] * 4
        self.modObjs = [None] * 4
        self.dropdowns = []
        self.widgets = {}
        self.inputObj = UserInput(self.widgets, self)

        self.activeNotes = []

        self.dialValues = {
            'attack': {
                'curr': params.defaultAttack,
                'min': params.minAttack,
                'max': params.maxAttack,
                'centerX': 260,
                'centerY': 260
            },
            'decay': {
                'curr': params.defaultDecay,
                'min': params.minDecay,
                'max': params.maxDecay,
                'centerX': 353.33,
                'centerY': 260
            },
            'sustain': {
                'curr': params.defaultSustain,
                'min': params.minSustain,
                'max': params.maxSustain,
                'centerX': 446.66,
                'centerY': 260
            },
            'release': {
                'curr': params.defaultRelease,
                'min': params.minRelease,
                'max': params.maxRelease,
                'centerX': 540,
                'centerY': 260
            }
        }
        self.sliderValues = {
            "volume": {
                "curr": params.volume,
                "min": params.minVolume,
                "max": params.maxVolume
            },
            "frequency": {
                "curr": params.freq,
                "min": params.minFreq,
                "max": params.maxFreq
            }
        }


def audioCallback(outdata, frames, time_info, status):
    global drawingSignal
    #global delayBuffer, delayIdx

    if status: 
        print(f'{status=}')
    
    if (stream.cpu_load > 0.25):
        print(f'cpu {stream.cpu_load}')
    signal = np.zeros(frames, dtype=np.float32)
    with lock:
        startTime = time.time()
        for note in state.activeNotes[:]:
            if note.dead:
                state.activeNotes.remove(note)
                continue
            signal = signal + note.generate(frames, startTime)
            #signal = normalize(signal, note.generate(frames, startTime)) 

    peak = np.max(np.abs(signal)) + 1e-10
    if peak > 1:
        targetGain = 1 / peak
    else:
        targetGain = 1     

    if targetGain < params.smoothedGain:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaAttack) + targetGain * params.alphaAttack 
    else:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaRelease) + targetGain * params.alphaRelease 

    params.smoothedGain = 1
    signal *= params.smoothedGain * state.sliderValues['volume']['curr'] * params.masterDamp
    peak = np.max(np.abs(signal))

   
    if peak > 1:
        print(f"clip {peak}")

    # # apply modulations
    # for mod in state.modObjs:
    #     if mod:
    #         mod.updateParam()

    # apply effects
    for effect in state.effectObjs:
        if effect:
            signal = effect.process(signal, frames)
    
    drawingSignal = signal.copy()
    if peak > 1:
        drawingSignal *= (1/peak * params.visualShrink)
    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)

def draw():
    midPt = 10+(params.panelHeight*3/8)
    incr = params.waveVisualIncrease[state.waveType]
    pad = 0
    leftEdge = 210 + pad
    rightEdge = 590 - pad
    numPoints = rightEdge - leftEdge
    points = []
    for x, y in enumerate(drawingSignal[numPoints::-1]):
        points.append(x+leftEdge) 
        heightForPoint = y*incr
        points.append(midPt + heightForPoint)
    canvas.delete("wave")

    canvas.create_line(points, fill=params.primaryToneLight, tag="wave", width=params.sineWidth)
    root.after(5, draw)


# called as "callback" function in Dropdown class
def onSelectMod(event, modType, slot, sourceObj):
    print(f"Clicked on {modType} goes to slot {slot}")  
    if modType == "oscillator":
        modObj = Oscillator(slot, canvas, state)
    elif modType == "envelope":
        modObj = Envelope(slot, canvas, state)
    
    state.modObjs[slot] = modObj

    sourceObj.removeDropdown()
    # instantiate object of corresponding effect class

# called as "callback" function in Dropdown class
def onSelectEffect(event, effectType: str, slot: int, sourceObj):
    print(f"Clicked on {effectType} goes to slot {slot}")  

    if effectType == "distortion":
        effectObj = Distortion(slot, canvas, state)

        #effectObj = Distortion(slot)
    elif effectType == "delay":
        effectObj = Delay(slot, canvas, state)
    elif effectType == "compressor":
        effectObj = Compressor(slot, canvas, state)
    elif effectType == "filter":
        effectObj = Filter(slot, canvas, state)

    state.effectObjs[slot-4] = effectObj
    sourceObj.removeDropdown()

def onPanelClick(event, panelTag):
    x, y = event.x, event.y
    slot = int(panelTag[-1])

    # Modulations
    if "mod" in panelTag:
        panelType = "mod"
        options = ["oscillator", "envelope"]
        callback = onSelectMod # CHANGE TO ON SELECT MOD

    # Effects
    elif "effect" in panelTag:
        panelType = "effect"
        options = ["distortion", "compressor", "delay", "filter"] 
        callback = onSelectEffect

    Dropdown(x, y, options, slot, panelType, callback, canvas, state)

def onWaveformTitleClick(event, titleObj):
    waves = ["sine", "square", "saw"]
    state.waveType = canvas.itemcget(titleObj, "text")

    waveIdx = waves.index(state.waveType)
    newIdx = (waveIdx + 1) % len(waves)
    newWave = waves[newIdx]

    diffCharacters = len(newWave) - len(state.waveType)
    distancePerChar = 12

    canvas.move(titleObj, distancePerChar * diffCharacters, 0)
    canvas.itemconfig(titleObj, text=newWave, justify="left")

    state.waveType = newWave

def buildGUI():
    global root, canvas, keysGUI
    # build root
    root = tk.Tk()    
    root.geometry("800x415+100+50")
    root.resizable(False, False)
    root.title("simplesine")

    canvas = tk.Canvas(root, width=800,height=415, bg="#2B2B2B")
    
    # build 4 sides of window border
    canvas.create_rectangle(0, 0, 800, 10, fill=params.primaryToneLight)
    canvas.create_rectangle(0, 395, 800, 415, fill=params.primaryToneLight)
    canvas.create_rectangle(0, 10, 10, 395, fill=params.primaryToneLight)
    canvas.create_rectangle(790, 10, 800, 395, fill=params.primaryToneLight)


    # info text
    infoText = canvas.create_text(400, 405, text="This texts displays the functionality of the hovered feature.", anchor='c', fill=params.primaryToneDark, font=("Terminal", 10))

    # build panels
    bgMid = canvas.create_rectangle(210, 10, 590, 395, fill=params.secondaryToneDark, outline=None)
    centerTitle = canvas.create_text(355, 305*1/8+10, text="simple", justify='left', font=("Terminal", 30, 'bold'), fill=params.primaryToneLight)
    #waveformRect = canvas.create_rectangle(425, 305*1/8+10, 490, 305*1/8+30, fill=params.primaryToneDark)
    waveformTitle = canvas.create_text(475, 305*1/8+10, text="sine", justify='left', font=("Terminal", 30, 'bold', 'underline'), fill=params.primaryToneLight, activefill="white", tags="waveform_tag")
    canvas.tag_bind(waveformTitle, "<Button-1>", lambda event, titleObj=waveformTitle: onWaveformTitleClick(event, titleObj))
    panelHeight = 305 # total height - 2 * border - keysHeight


    rightPanels = []
    leftPanelLines = []
    rightPanelLines = []
    panelLineHeight = 3
    for i in range(0,4):
        y = (panelHeight/4*i) + 10
        y2 = (panelHeight/4*(i+1)) + 10

        tagName = f"modPanel{i}"

        leftPanelLines.append(canvas.create_rectangle(10, y, 210, y+panelLineHeight, fill=params.secondaryToneDark))
        panel = canvas.create_rectangle(10, y+panelLineHeight, 210, y2+panelLineHeight, fill=params.secondaryToneLight, activefill=params.primaryToneDark, tags=tagName)
        canvas.tag_bind(tagName, "<Button-1>", lambda event, currentPanel=tagName: onPanelClick(event, currentPanel))

        tagName = f"effectPanel{i+4}"
        panel = canvas.create_rectangle(590, y+panelLineHeight, 790, y2+panelLineHeight, fill=params.secondaryToneLight, activefill=params.primaryToneDark, tags=tagName)
        canvas.tag_bind(tagName, "<Button-1>", lambda event, currentPanel=tagName: onPanelClick(event, currentPanel))
        rightPanelLines.append(canvas.create_rectangle(590, y, 790, y+panelLineHeight, fill=params.secondaryToneDark))



    modulationsTxt = canvas.create_text(110, 30, text="modulations", justify='center', font=("Terminal", 16, 'bold'), fill=params.secondaryToneDark)
    effectsTxt = canvas.create_text(690, 30, text="effects", justify='center', font=("Terminal", 16, 'bold'), fill=params.secondaryToneDark)

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
   
class Slider:
    def __init__(self, name):
        self.name = name
        
        #knobWidth = params.sliders[self.name]['knobWidth']

        self.widthPad = 20
        self.left = params.sliders[self.name]['left'] - self.widthPad
        self.right = params.sliders[self.name]['right'] + self.widthPad
        self.yPos = params.sliders[self.name]['yPos']
        self.knobHeight = params.sliders[self.name]['knobHeight']

        height = params.sliders[self.name]['height']
        knobWidth = params.sliders[self.name]['knobWidth']
        
        textPad = 20
        hitboxSizeMultiplier = 4

        current = state.sliderValues[self.name]['curr']
        minimum = state.sliderValues[self.name]['min']
        maximum = state.sliderValues[self.name]['max']

        normalizedCurrentValue = (current - minimum) / (maximum - minimum)

        tagName = f"{self.name}_tag"
        self.bg = canvas.create_rectangle(self.left, self.yPos-height, self.right, self.yPos +height, fill=params.primaryToneDark,outline="black")
        #self.knob = canvas.create_rectangle(self.left+(self.right-self.left)/2-knobWidth/2, self.yPos-self.knobHeight , self.left+(self.right-self.left)/2+knobWidth/2, self.yPos+self.knobHeight , fill=params.primaryToneLight,outline="black")
        self.knob = canvas.create_rectangle(self.left+(self.right-self.left)*normalizedCurrentValue-knobWidth/2, self.yPos-self.knobHeight ,self.left+(self.right-self.left)*normalizedCurrentValue+knobWidth/2, self.yPos+self.knobHeight , fill=params.primaryToneLight,outline="black")
        self.text = canvas.create_text(self.left+(self.right-self.left)/2, self.yPos +textPad, text=f"{self.name}: {state.sliderValues[self.name]['curr']:.2f}", fill="white")
        self.hitbox = canvas.create_rectangle(self.left, self.yPos -height*hitboxSizeMultiplier, self.right, self.yPos +height*hitboxSizeMultiplier, fill="", outline="", tag=tagName)
        canvas.tag_bind(tagName, "<Button-1>", lambda event: state.inputObj.mouseClicked(event, self.name))


    def update(self, clickPoint, mousePoint):
        global volume, pitch

        # update knob position
        mouse_x = mousePoint[0]
        slider_x = min(self.right, max(self.left, mouse_x))
        canvas.moveto(self.knob, slider_x-params.sliders[self.name]['knobWidth']/2, params.sliders[self.name]['yPos']-params.sliders[self.name]['knobHeight'])

        # so figure out 
        minParameterValue = state.sliderValues[self.name]['min']
        maxParameterValue = state.sliderValues[self.name]['max']

        # how far along the slider_x is between min and max
        sliderPercent = (slider_x-self.left)/(self.right-self.left)

        #masterVolume = minParameterValue + (maxParameterValue - minParameterValue) * sliderPercent
        state.sliderValues[self.name]['curr'] = minParameterValue + (maxParameterValue - minParameterValue) * sliderPercent
        #volume = params.minVolume + (params.maxVolume - params.minVolume) * sliderPercent
        #print(f"{self.name}: {sliderValues[self.name]['curr']}")


        canvas.itemconfig(self.text, text=f"{self.name}: {state.sliderValues[self.name]['curr']:.2f}")
        
        self.left  + (slider_x/self.right)


class UserInput():
    def __init__(self, widgets, state):
        self.mousePoint: tuple[int, int] = None
        self.clickPoint: tuple[int, int] = None
        self.widgets = widgets
        self.activeWidget = None

    def mouseClicked(self, event, elementName):
        print(f'{elementName=}')
        self.activeWidget = self.widgets[elementName]
        self.clickPoint = self.mousePoint

        if self.activeWidget.name in state.sliderValues:
            self.widgets[self.activeWidget.name].update(self.clickPoint, self.mousePoint)

    def mouseSecondaryPressed(self, event):
        pass
        #removePopup()

    def mouseReleased(self, event):
        self.activeWidget = None
        print(event.x, event.y)

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
            transpose(amnt)
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
        attack = state.dialValues['attack']['curr']
        decay = state.dialValues['decay']['curr']
        sustain = state.dialValues['sustain']['curr']
        release = state.dialValues['release']['curr']

        ''' Returns correct amplitude of note based on time in envelope '''
        lifetime = t - self.start
        if not self.released:
            # attack phase
            if lifetime < attack:
                #print("attack", lifetime)
                ratio = lifetime / attack
                return self.getAmp(0, peakVolume, ratio)
            # decay phase
            elif lifetime < (attack + decay):
                #print("decay", lifetime)
                ratio = (lifetime - attack) / decay
                return self.getAmp(peakVolume, peakVolume * sustain, ratio)
            # sustain phase
            else:
                #print("sustain", lifetime)
                self.amp = peakVolume * sustain
                return peakVolume * sustain
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

        phaseIncrement = 2 * np.pi * (self.freq + state.sliderValues['frequency']['curr'])/ params.samplerate # radians per sample travelled
        phases = np.arange(frames) * phaseIncrement + self.phase

        if state.waveType == "sine":
            signal = np.sin(phases)
        elif state.waveType == "square":
            signal = np.sign(np.sin(phases)) * params.squareAudioDamp
        elif state.waveType == "saw":
            signal = (2 * ((phases / (2 * np.pi)) % 1) - 1) * params.sawAudioDamp
        signal *= amplitudes

        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)

        return signal




# class Modulation(PanelComponent):
#     def __init__(self, title, slot):
#         super().__init__(title, slot)

#     def createParamListener(self):
#         xPad = 140
#         yPad = 40
#         paramText = canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad, text="param", font=('Terminal', 10, 'bold', 'underline'), anchor ="w", fill=params.primaryToneLight, activefill="white")
#         #canvas.tag_bind(typeText, "<Button-1>", lambda event, options=options: self.initDropdown(event, options))

#         self.currentParamText = canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad + 20, text="None", font=('Terminal', 7),anchor="w", fill=params.primaryToneLight)
#         self.canvasObjects.append(paramText)
#         self.canvasObjects.append(self.currentParamText) 
    
# class Oscillator(Modulation):
#     def __init__(self, slot):
#         super().__init__(title="oscillator", slot=slot)
#         self.slot = slot
#         self.rate = 50
#         self.depth = 0.5
#         self.param = None

#         PanelComponent.buildDial(
#             self,
#             name = f"oscillator{self.slot}Rate", 
#             centerX = self.topLeftX + params.panelWidth * 1/4,
#             centerY = self.topLeftY + params.panelHeight / 8,
#             diameter = 30,
#             minValue = 1e-9,
#             maxValue = 20,
#             sourceObj = self,
#             parameter = "rate",
#             label="rate ",
#             units=" Hz",
#             ratioRamp = 2
#         )

#         PanelComponent.buildDial(
#             self,
#             name = f"oscillator{self.slot}Depth", 
#             centerX = self.topLeftX + params.panelWidth * 2/4,
#             centerY = self.topLeftY + params.panelHeight / 8,
#             diameter = 30,
#             minValue = 0,
#             maxValue = 1,
#             sourceObj = self,
#             parameter = "depth",
#             label="depth "
#         )

#         super().createParamListener()


# class Envelope(Modulation):
#     def __init__(self, slot):
#         super().__init__(title="envelope", slot=slot)
#         self.slot = slot
#         self.attack = 1
#         self.decay = 1
#         self.sustain = 1
#         self.release = 1
#         self.param = None

#         xPad = -15
#         PanelComponent.buildDial(
#             self,
#             name = f"envelope{self.slot}Attack", 
#             centerX = self.topLeftX + params.panelWidth * 1/6 + xPad,
#             centerY = self.topLeftY + params.panelHeight / 8,
#             diameter = 20,
#             minValue = 1e-9,
#             maxValue = 5,
#             sourceObj = self,
#             parameter = "attack",
#             label="A=",
#             ratioRamp=2
#         )

#         PanelComponent.buildDial(
#             self,
#             name = f"envelope{self.slot}Decay", 
#             centerX = self.topLeftX + params.panelWidth * 2/6 + xPad,
#             centerY = self.topLeftY + params.panelHeight / 8,
#             diameter = 20,
#             minValue = 1e-9,
#             maxValue = 5,
#             sourceObj = self,
#             parameter = "decay",
#             label="D=",
#             ratioRamp=2
#         )

#         PanelComponent.buildDial(
#             self,
#             name = f"envelope{self.slot}Sustain", 
#             centerX = self.topLeftX + params.panelWidth * 3/6 + xPad,
#             centerY = self.topLeftY + params.panelHeight / 8,
#             diameter = 20,
#             minValue = 1e-9,
#             maxValue = 1,
#             sourceObj = self,
#             parameter = "sustain",
#             label="S=",
#         )

#         PanelComponent.buildDial(
#             self,
#             name = f"envelope{self.slot}Release", 
#             centerX = self.topLeftX + params.panelWidth * 4/6 + xPad,
#             centerY = self.topLeftY + params.panelHeight / 8,
#             diameter = 20,
#             minValue = 1e-9,
#             maxValue = 5,
#             sourceObj = self,
#             parameter = "release",
#             label="R=",
#             ratioRamp=2
#         )

#         super().createParamListener()



# NOTES PLAYED/RELEASED
def notePlayed(globalNoteID):
    with lock:
        freq = utils.NOTE_TO_FREQ[globalNoteID]
        state.activeNotes.append(Note(freq))
        highlightNote(globalNoteID, "note_on")

def noteReleased(globalNoteID):
    with lock:
        freq = utils.NOTE_TO_FREQ[globalNoteID]
        for note in state.activeNotes:
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

def transpose(amount: int):
    global lowestNote
    lowestNote += amount
    print(f'New {lowestNote=}')

main()