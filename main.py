import tkinter as tk
import numpy as np
import sounddevice as sd
import threading, mido, utils, params, time, os


# apparent global values
attack = params.defaultAttack
decay = params.defaultDecay
sustain = params.defaultSustain
release = params.defaultRelease
peakVolume = params.peakVolume
volume = params.volume

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
sliderValues = {
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

    widgets['volume'] = Slider('volume')
    widgets['frequency'] = Slider('frequency')

    # bind keyboard input to callback function
    inputObj = UserInput(widgets)
    root.bind("<KeyPress>", inputObj.onKeyPressed)
    root.bind("<KeyRelease>", inputObj.onKeyReleased)
    root.bind("<Motion>", inputObj.mouseMotion)
    root.bind("<ButtonRelease-1>", inputObj.mouseReleased)

    root.after(500, draw)
    # listen for midi input
    midiThread = threading.Thread(target=inputObj.midiListener)
    midiThread.start()
    # start audio stream
    stream = sd.OutputStream(samplerate=params.samplerate, channels=2, callback=audioCallback, blocksize=params.blocksize)
    stream.start()

    root.mainloop()
    os.system('xset r on')

def audioCallback(outdata, frames, time_info, status):
    global drawingSignal
    if status: 
        print(f'{status=}')
    
    if (stream.cpu_load > 0.25):
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

    params.smoothedGain = 1
    #print(f'{targetGain=}')
    signal *= params.smoothedGain * sliderValues['volume']['curr'] * params.masterDamp
    peak = np.max(np.abs(signal))

    
    
    if peak > 1:
        print(f"clip {peak}")


    def hardClip(signal, threshold=0.2):

        return np.clip(signal, -threshold, threshold)

    def softClip(signal, overdrive):
        signal *= overdrive
        return np.tanh(signal)
    
    def halfWave(signal):
        return np.maximum(0, signal)

    # doesn't work with envelopes
    def square(signal):

        return np.sign(signal) * 0.5 
    
    #signal = softClip(signal, 1.5)
    #distortedSignal = hardClip(signal, 0.2)

    

    distortedSignal = halfWave(signal)
    signal = (1.0*signal) + (0*distortedSignal)
    #print(np.sign(signal))
    drawingSignal = signal.copy()
    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)
def draw():

    maxSineHeight = 50
    minSineHeight = 305*3/8+10
    pad = 0
    leftEdge = 210 + pad
    rightEdge = 590 - pad
    numPoints = rightEdge - leftEdge

    # 3/8ths of way down panel + border
    #canvas.create_line(leftEdge, 305*3/8+10, rightEdge, 305*3/8+10, fill=params.primaryToneDark, width=2)

    #canvas.create_line(100, 200, 200, 200, fill="orange")
    #canvas.create_line(210, 100, 590, 100, fill="yellow")
    #canvas.create_line(100, 200, 200, 200, fill="yellow")

    points = []
    for x, y in enumerate(drawingSignal[:numPoints]):
        points.append(x+leftEdge) 
        points.append(minSineHeight + y*maxSineHeight) # this equation doesn't work how I think it does
    canvas.delete("wave")
    canvas.create_line(points, fill=params.primaryToneLight, tag="wave", width=params.sineWidth)

    root.after(10, draw)



effects = [None] * 4
mods = [None] * 4

popupObjects = []

def removePopup():
    for obj in popupObjects:
        canvas.delete(obj)

def onPopupModTextClick(event, piece, slot):
    print(f"Clicked on {piece} goes to slot {slot}")  
    removePopup()


def onPopupTextEnter(event, piece):
    canvas.itemconfig(piece, fill=params.primaryToneLight)

def onPopupTextLeave(event, piece):
    canvas.itemconfig(piece, fill=params.primaryToneDark)


def createPopup(x, y, panelType, slot):
    removePopup()
    # prevent pop-up from going off-screen
    print(x)

    if panelType == "effect":
        x = max(min(x, 750), 630)
    elif panelType == "mod":
        x = max(min(x, 170), 50)
    #x = max(x, 20)
    popupWidth = 80
    popupHeight = 90
    effectTexts = ["distortion", "chorus", "delay", "filter"] 
    modTexts = ["oscillator", "envelope"]
    pieceHeight = popupHeight / len(effectTexts)
    #popup = canvas.create_rectangle(x-(popupWidth/2), y, x+(popupWidth/2), y+(popupHeight/2), fill="green")

    delta_y = 25
    i = 0
    padFromTop = 12


    if panelType == "effect":
        for effectText in effectTexts:
            piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
            textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=effectText, font=("Terminal", 9), fill="white")

            canvas.tag_bind(piece, "<Button-1>", lambda event, effectName=effectText, slotArg=slot: onPopupModTextClick(event, effectName, slotArg))
            canvas.tag_bind(textObj, "<Button-1>", lambda event, effectName=effectText, slotArg=slot: onPopupModTextClick(event, effectName, slotArg))
            canvas.tag_bind(textObj, "<Enter>", lambda event, pieceObj=piece: onPopupTextEnter(event, pieceObj))
            canvas.tag_bind(textObj, "<Leave>", lambda event, pieceObj=piece: onPopupTextLeave(event, pieceObj))

            popupObjects.append(piece)
            popupObjects.append(textObj)

            i += 1

    elif panelType == "mod":
        for modText in modTexts:
            print(f'{modText=}')
            piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
            textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=modText, font=("Terminal", 9), fill="white")
            
            canvas.tag_bind(piece, "<Button-1>", lambda event, modName=modText, slotArg=slot: onPopupModTextClick(event, modName, slotArg))
            canvas.tag_bind(textObj, "<Button-1>", lambda event, modName=modText, slotArg=slot: onPopupModTextClick(event, modName, slotArg))
            canvas.tag_bind(textObj, "<Enter>", lambda event, pieceObj=piece: onPopupTextEnter(event, pieceObj))
            canvas.tag_bind(textObj, "<Leave>", lambda event, pieceObj=piece: onPopupTextLeave(event, pieceObj))

            popupObjects.append(piece)
            popupObjects.append(textObj)

            i += 1


def onPopupClick():
    
    pass

def createEffect():
    pass
def createModulation():
    pass

def onDestroyPanel():
    # update effects or mod dict
    # remove element from canvas
    pass

def onPanelClick(event, panelTag):#, panelName):
    x, y = event.x, event.y
    slot = int(panelTag[-1])

    # Modulations
    if "mod" in panelTag:
        panelType = "mod"
        panelDict = mods

    # Effects
    elif "effect" in panelTag:
        panelType = "effect"
        panelDict = effects

    if panelDict[slot]:
        print(f"{panelType}{slot} already full")
        return

    #panelDict[slot] = "Full"

    createPopup(x, y, panelType, slot)

    print(f'{panelDict}{slot}')
    # print(event)
    # print(panelTag)

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
    centerTitle = canvas.create_text(400, 305*1/8+10, text="simplesine", justify='center', font=("Terminal", 30, 'bold'), fill=params.primaryToneLight)
    
    panelHeight = 305 # total height - 2 * border - keysHeight
    leftPanelLines = []
    leftPanels = []
    rightPanelLines = []
    panelLineHeight = 3
    for i in range(0,4):
        y = (panelHeight/4*i) + 10
        y2 = (panelHeight/4*(i+1)) + 10

        tagName = f"modPanel{i}"

        leftPanelLines.append(canvas.create_rectangle(10, y, 210, y+panelLineHeight, fill=params.secondaryToneDark))
        panel = canvas.create_rectangle(10, y+panelLineHeight, 210, y2+panelLineHeight, fill=params.secondaryToneLight, activefill=params.primaryToneDark, tags=tagName)
        print(f"Adding bind to {tagName} tag")
        canvas.tag_bind(tagName, "<Button-1>", lambda event, currentPanel=tagName: onPanelClick(event, currentPanel))

        tagName = f"effectPanel{i}"
        panel = canvas.create_rectangle(590, y+panelLineHeight, 790, y2+panelLineHeight, fill=params.secondaryToneLight, activefill=params.primaryToneDark, tags=tagName)
        canvas.tag_bind(tagName, "<Button-1>", lambda event, currentPanel=tagName: onPanelClick(event, currentPanel))


        #leftPanels.append(panel)
        #print(f"leftPanel{panelNum}")
        #canvas.tag_bind(f"leftPanel{panelNum}", "<Button-1>", lambda event: onPanelClick(event, leftPanels[panelNum]))
        #print(f'{canvas.gettags(panel)=}')
        #canvas.tag_bind(tagName, "<Button-1>", lambda event: inputObj.mouseClicked(event, self.name))

        #panel.bind("<Hover>", lambda event: onPanelMouseHover(event, panel))
        #tagName = f"rightPanel{panelNum}"
        rightPanelLines.append(canvas.create_rectangle(590, y, 790, y+panelLineHeight, fill=params.secondaryToneDark))
        #panel = canvas.create_rectangle(590, y+panelLineHeight, 790, y2+panelLineHeight, fill=params.secondaryToneLight, activefill=params.primaryToneDark, tags=tagName)

    # print(leftPanels)
    # for i in range(4):
    #     print(f'{i=}')
    #     canvas.tag_bind(f"leftPanel{i}", "<Button-1>", lambda event: onPanelClick(event, leftPanels[i]))

    # for panel in leftPanels:
    #     canvas.tag_bind(f"leftPanel{panelNum}", "<Button-1>", lambda event: onPanelClick(event, leftPanels[panelNum]))

    #     print(canvas.gettags(panel))

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
            self.text = canvas.create_text(dialCenters_x[self.name], dialCenter_y+(dialHeight/2)+textPadding, text=f'{dialValues[self.name]['curr']*100:.2f}%', fill="white")
        
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
            canvas.itemconfig(self.text, text=f'{dialValues[self.name]['curr']*100:.2f}%')
    
    def getStartExtent(self, name):
        env = dialValues[name]
        return -360 * ((env['curr']-env['min']) / (env['max']-env['min']))**(1/2)


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

        current = sliderValues[self.name]['curr']
        minimum = sliderValues[self.name]['min']
        maximum = sliderValues[self.name]['max']

        normalizedCurrentValue = (current - minimum) / (maximum - minimum)

        tagName = f"{self.name}_tag"
        self.bg = canvas.create_rectangle(self.left, self.yPos-height, self.right, self.yPos +height, fill=params.primaryToneDark,outline="black")
        #self.knob = canvas.create_rectangle(self.left+(self.right-self.left)/2-knobWidth/2, self.yPos-self.knobHeight , self.left+(self.right-self.left)/2+knobWidth/2, self.yPos+self.knobHeight , fill=params.primaryToneLight,outline="black")
        self.knob = canvas.create_rectangle(self.left+(self.right-self.left)*normalizedCurrentValue-knobWidth/2, self.yPos-self.knobHeight ,self.left+(self.right-self.left)*normalizedCurrentValue+knobWidth/2, self.yPos+self.knobHeight , fill=params.primaryToneLight,outline="black")
        self.text = canvas.create_text(self.left+(self.right-self.left)/2, self.yPos +textPad, text=f"{self.name}: {sliderValues[self.name]['curr']:.2f}", fill="white")
        self.hitbox = canvas.create_rectangle(self.left, self.yPos -height*hitboxSizeMultiplier, self.right, self.yPos +height*hitboxSizeMultiplier, fill="", outline="", tag=tagName)
        canvas.tag_bind(tagName, "<Button-1>", lambda event: inputObj.mouseClicked(event, self.name))


    def update(self, clickPoint, mousePoint):
        global volume, pitch

        # update knob position
        mouse_x = mousePoint[0]
        slider_x = min(self.right, max(self.left, mouse_x))
        canvas.moveto(self.knob, slider_x-params.sliders[self.name]['knobWidth']/2, params.sliders[self.name]['yPos']-params.sliders[self.name]['knobHeight'])

        # so figure out 
        minParameterValue = sliderValues[self.name]['min']
        maxParameterValue = sliderValues[self.name]['max']

        # how far along the slider_x is between min and max
        sliderPercent = (slider_x-self.left)/(self.right-self.left)

        #masterVolume = minParameterValue + (maxParameterValue - minParameterValue) * sliderPercent
        sliderValues[self.name]['curr'] = minParameterValue + (maxParameterValue - minParameterValue) * sliderPercent
        #volume = params.minVolume + (params.maxVolume - params.minVolume) * sliderPercent
        #print(f"{self.name}: {sliderValues[self.name]['curr']}")


        canvas.itemconfig(self.text, text=f"{self.name}: {sliderValues[self.name]['curr']:.2f}")


        # 500 - 200 / (300) = 1
        # 200 - 200 / 300 =  0



        # slider_x = 200, volume = minVolume

        # slider_x = 500, volume = maxVolume
        
        self.left  + (slider_x/self.right)
        # based on knob position, change global variables
        pass


class UserInput():
    def __init__(self, widgets):
        self.mousePoint: tuple[int, int] = None
        self.clickPoint: tuple[int, int] = None
        self.widgets = widgets
        self.activeWidget = None

    def mouseClicked(self, event, elementName):
        self.activeWidget = self.widgets[elementName]
        self.clickPoint = self.mousePoint

        if self.activeWidget.name in sliderValues:
            self.widgets[self.activeWidget.name].update(self.clickPoint, self.mousePoint)

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

        phaseIncrement = 2 * np.pi * (self.freq + sliderValues['frequency']['curr'])/ params.samplerate # radians per sample travelled
        phases = np.arange(frames) * phaseIncrement + self.phase


        signal = amplitudes * np.sin(phases)

        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)

        # if -0.5 <= self.phase <= 0.5:
            
        #     print(self.phase)

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

def transpose(amount: int):
    global lowestNote
    lowestNote += amount
    print(f'New {lowestNote=}')

main()