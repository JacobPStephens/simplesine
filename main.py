import tkinter as tk
import numpy as np
import sounddevice as sd
import threading, mido, utils, params, time, os

import random

# global synth settings
attack = params.defaultAttack
decay = params.defaultDecay
sustain = params.defaultSustain
release = params.defaultRelease
peakVolume = params.peakVolume
volume = params.volume

lowestNote = params.defaultLowestNote

# tmp = int(params.samplerate * params.delayTime)
# print(f'{tmp=}{type(tmp)=}')
# delaySamples = int(params.samplerate * params.delayTime)
# delayBuffer = np.zeros(delaySamples)

dialValues = {
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
    global lock, activeNotes, stream, inputObj, widgets

    os.system('xset r off')
    
    buildGUI()

    activeNotes = []
    lock = threading.Lock()

    # build widgets 
    widgets = {}
    # ADSR knobs
    
    for name in ['attack', 'decay', 'sustain', 'release']:
        dialType = dialValues[name]
        label = ""
        if name == "sustain":
            units = ""
        else:
            units = "s"
        widgets[name] = Dial(dialType['centerX'], dialType['centerY'], params.dialWidth, dialType['min'], dialType['max'], name, label="", units=units, isADSR=True)

        #widgets[name] = Dial(name)

    widgets['volume'] = Slider('volume')
    widgets['frequency'] = Slider('frequency')

    # bind keyboard input to callback function
    inputObj = UserInput(widgets)
    root.bind("<KeyPress>", inputObj.onKeyPressed)
    root.bind("<KeyRelease>", inputObj.onKeyReleased)
    root.bind("<Motion>", inputObj.mouseMotion)
    root.bind("<ButtonRelease-1>", inputObj.mouseReleased)
    root.bind("<Button-3>", inputObj.mouseSecondaryPressed)

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
    #global delayBuffer, delayIdx

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
    if peak > 1:
        targetGain = 1 / peak
    else:
        targetGain = 1     

    if targetGain < params.smoothedGain:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaAttack) + targetGain * params.alphaAttack 
    else:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaRelease) + targetGain * params.alphaRelease 

    params.smoothedGain = 1
    signal *= params.smoothedGain * sliderValues['volume']['curr'] * params.masterDamp
    peak = np.max(np.abs(signal))

    # def compressor():
    #     peak = np.max(np.abs(signal)) + 1e-10
    #     if peak > threshold:

            
        # for sample in signal:
        #     if sample > threshold:
        #         sample = sample / ratio


    
    if peak > 1:
        print(f"clip {peak}")

    for effect in effectObjs:
        if effect:
            signal = effect.process(signal, frames)
    
    drawingSignal = signal.copy()
    if peak > 1:
        drawingSignal *= (1/peak * params.visualShrink)
    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)

def draw():

    ceiling = 50
    floor = -50
    midPt = 10+(params.panelHeight*3/8)
    incr = params.waveVisualIncrease[waveType]

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
    for x, y in enumerate(drawingSignal[numPoints::-1]):
        points.append(x+leftEdge) 

        heightForPoint = y*incr

        # heightForPoint = max(floor, min(heightForPoint, ceiling))
        # # if heightForPoint > floor or heightForPoint < ceiling:
        # #     heightForPoint = m
        # #     print(f'{y=} out of bounds')
        points.append(midPt + heightForPoint) # this equation doesn't work how I think it does
    canvas.delete("wave")
    

    canvas.create_line(points, fill=params.primaryToneLight, tag="wave", width=params.sineWidth)


    root.after(5, draw)



#EFFECTS: list[callable] = [None] * 4

effectObjs = [None] * 4
mods = [None] * 4
waveType = "sine"

popupObjects = []

def removePopup():
    for obj in popupObjects:
        canvas.delete(obj)



def onSelectEffect(event, effectName: str, slot: int, sourceObj):
    effectNameToClass = {
        "distortion": Distortion,
        "delay": Delay,
        "compressor": Compressor,
        "filter": Filter

    }
    print(f"Clicked on {effectName} goes to slot {slot}")  

    # instantiate object of corresponding effect class
    EffectClass = effectNameToClass[effectName]
    effectObjs[slot] = EffectClass(slot)

    sourceObj.removeDropdown()

def colorChange(event, piece, color):
    canvas.itemconfig(piece, fill=color)

# def onLeaveColorChange(event, piece, color):
#     canvas.itemconfig(piece, fill=params.primaryToneDark)


class Dropdown:
    global canvas
    def __init__(self, x: int, y: int, options: list[str], slot: int, panelType: str, callback: callable):
        self.options = options
        self.objects = []
        self.createDropdown(x, y, slot, panelType, callback)

    def createDropdown(self, x, y, slot, panelType, callback):

        popupWidth = 80
        topPadding = 12
        elementHeight = 25

        for i, option in enumerate(self.options):
            #piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
            piece = canvas.create_rectangle(x-popupWidth/2, y+elementHeight*i, x+popupWidth/2, y+elementHeight*(i+1), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
            textObj = canvas.create_text(x, y+elementHeight*i+topPadding,text=option, font=("Terminal", 9), fill="white")
            #textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=effectText, font=("Terminal", 9), fill="white")
            canvas.tag_bind(piece, "<Button-1>", lambda event, optionName=option, slotArg=slot: callback(event, optionName, slotArg, self))
            canvas.tag_bind(textObj, "<Button-1>", lambda event, optionName=option, slotArg=slot: callback(event, optionName, slotArg, self))

            canvas.tag_bind(textObj, "<Enter>", lambda event, obj=piece, color=params.primaryToneLight: colorChange(event, obj, color))
            canvas.tag_bind(textObj, "<Leave>", lambda event, obj=piece, color=params.primaryToneDark: colorChange(event, obj, color))

            self.objects.append(piece)
            self.objects.append(textObj)        

    def removeDropdown(self):
        for obj in self.objects:
            canvas.delete(obj)
        self.objects = []
        print('delted popup line 286s')
    
# def createPopup(x, y, panelType, slot, sourceObj=None):
#     removePopup()
#     # prevent pop-up from going off-screen

#     if panelType == "effect":
#         x = max(min(x, 750), 630)
#     elif panelType == "mod":
#         x = max(min(x, 170), 50)

#     elif panelType == "distortion":
#         pass
#     #x = max(x, 20)
#     popupWidth = 80
#     popupHeight = 90
#     effectTexts = ["distortion", "compressor", "delay", "filter"] 
#     modTexts = ["oscillator", "envelope"]
#     distortionTexts = ["soft clip", "hard clip", "half wave"]
#     filterTexts = ["low-pass", "high-pass"]
#     waveTexts = ["sine", "square", "saw"]
#     pieceHeight = popupHeight / len(effectTexts)
#     #popup = canvas.create_rectangle(x-(popupWidth/2), y, x+(popupWidth/2), y+(popupHeight/2), fill="green")

#     delta_y = 25
#     i = 0
#     padFromTop = 12

#     if panelType == "effect":
#         for effectText in effectTexts:
#             piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
#             textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=effectText, font=("Terminal", 9), fill="white")
            

#             canvas.tag_bind(piece, "<Button-1>", lambda event, effectName=effectText, slotArg=slot: onSelectEffect(event, effectName, slotArg))
#             canvas.tag_bind(textObj, "<Button-1>", lambda event, effectName=effectText, slotArg=slot: onSelectEffect(event, effectName, slotArg))
#             canvas.tag_bind(textObj, "<Enter>", lambda event, obj=piece, color=params.primaryToneLight: colorChange(event, obj, color))
#             canvas.tag_bind(textObj, "<Leave>", lambda event, obj=piece, color=params.primaryToneDark: colorChange(event, obj, color))

#             popupObjects.append(piece)
#             popupObjects.append(textObj)
#             i += 1



#     # elif panelType == "mod":
#     #     for waveText in modTexts:
#     #         piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
#     #         textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=waveText, font=("Terminal", 9), fill="white")
            
#     #         canvas.tag_bind(piece, "<Button-1>", lambda event, modName=waveText, slotArg=slot, ownerObj=sourceObj: onPopupModTextClick(event, modName, slotArg))
#     #         canvas.tag_bind(textObj, "<Button-1>", lambda event, modName=waveText, slotArg=slot, ownerObj=sourceObj: onPopupModTextClick(event, modName, slotArg))
#     #         canvas.tag_bind(textObj, "<Enter>", lambda event, pieceObj=piece: hoverColorChange(event, pieceObj))
#     #         canvas.tag_bind(textObj, "<Leave>", lambda event, pieceObj=piece: onLeaveColorChange(event, pieceObj))

#     #         popupObjects.append(piece)
#     #         popupObjects.append(textObj)
#     #         i += 1


#     elif panelType == "distortion":
#         assert sourceObj
#         for distortionText in distortionTexts:
#             piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black") 
#             textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=distortionText, font=("Terminal", 9), fill="white")

#             canvas.tag_bind(piece, "<Button-1>", lambda event, distortionType=distortionText: sourceObj.onSelectDistortionType(event, distortionType))
#             canvas.tag_bind(textObj, "<Button-1>", lambda event, distortionType=distortionText: sourceObj.onSelectDistortionType(event, distortionType))
#             canvas.tag_bind(textObj, "<Enter>", lambda event, pieceObj=piece, color=params.primaryToneLight: colorChange(event, pieceObj, color))
#             canvas.tag_bind(textObj, "<Leave>", lambda event, pieceObj=piece, color=params.primaryToneDark: colorChange(event, pieceObj, color))

#             popupObjects.append(piece)
#             popupObjects.append(textObj)

#             i += 1
#     elif panelType == "filter":

#         for filterText in filterTexts:
#             piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black") 
#             textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=filterText, font=("Terminal", 9), fill="white")
            
#             canvas.tag_bind(piece, "<Button-1>", lambda event, filterType=filterText: sourceObj.onSelectFilterType(event, filterType))
#             canvas.tag_bind(textObj, "<Button-1>", lambda event, filterType=filterText: sourceObj.onSelectFilterType(event, filterType))
#             canvas.tag_bind(textObj, "<Enter>", lambda event, pieceObj=piece, color=params.primaryToneLight: colorChange(event, pieceObj, color))
#             canvas.tag_bind(textObj, "<Leave>", lambda event, pieceObj=piece, color=params.primaryToneDark: colorChange(event, pieceObj, color))

#             popupObjects.append(piece)
#             popupObjects.append(textObj)

#             i += 1
  

def onPanelClick(event, panelTag):
    x, y = event.x, event.y
    slot = int(panelTag[-1])

    # Modulations
    if "mod" in panelTag:
        panelType = "mod"
        options = ["oscillator", "envelope"]
        callback = None # CHANGE TO ON SELECT MOD

    # Effects
    elif "effect" in panelTag:
        panelType = "effect"
        options = ["distortion", "compressor", "delay", "filter"] 
        callback = onSelectEffect

    Dropdown(x, y, options, slot, panelType, callback)

    #createPopup(x, y, panelType, slot)


def onWaveformTitleClick(event, titleObj):
    global waveType
    waves = ["sine", "square", "saw"]
    waveType = canvas.itemcget(titleObj, "text")

    waveIdx = waves.index(waveType)
    newIdx = (waveIdx + 1) % len(waves)
    newWave = waves[newIdx]

    


    diffCharacters = len(newWave) - len(waveType)
    distancePerChar = 12

    canvas.move(titleObj, distancePerChar * diffCharacters, 0)
    canvas.itemconfig(titleObj, text=newWave, justify="left")

    createPopup(event.x, event.y, "title", None)

    waveType = newWave

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

        tagName = f"effectPanel{i}"
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
   
class Dial:
    def __init__(self, centerX, centerY, diameter, minValue, maxValue, name, label, units, isADSR, sourceObj=None, parameter=None):
        self.centerX = centerX
        self.centerY = centerY
        self.diameter = diameter
        self.minValue = minValue
        self.maxValue = maxValue
        self.name = name
        self.label = label
        self.units = units
        self.isADSR = isADSR
        self.ratioRamp = 2 if self.isADSR else 1
        self.sourceObj = sourceObj
        self.parameter = parameter
        self.createDial()

    def createDial(self):
        if self.isADSR:
            textPadding = params.textPaddingADSR
        else:
            textPadding = params.textPaddingSmall
        startExtent = self.getStartExtent()
        tagName = f'{self.name}_tag'
        dialCoords = [self.centerX-(self.diameter/2), self.centerY-(self.diameter/2), self.centerX+(self.diameter/2), self.centerY+(self.diameter/2)]
        self.bg = canvas.create_oval(dialCoords, fill=params.primaryToneDark, outline="black", width=1.5, tags=tagName)
        self.arc = canvas.create_arc(dialCoords, fill=params.primaryToneLight, start= 270, extent= startExtent, tags=tagName)
        if self.isADSR:
            self.text = canvas.create_text(self.centerX,self.centerY+(self.diameter/2)+textPadding, text=f"{dialValues[self.name]['curr']:.2f}{self.units}", fill="white")
        else:
            self.text = canvas.create_text(self.centerX,self.centerY+(self.diameter/2)+textPadding, text=f"{self.label}{dialValues[self.name]['curr']:.2f}{self.units}", font=("TKDefaultFont", 6), fill="white")
        canvas.tag_bind(tagName, "<Button-1>", lambda event: inputObj.mouseClicked(event, self.name))       


    def update(self, clickPoint, mousePoint):
        # calculate dial angle using user's mouse location
        verticalDiff = clickPoint[1] - mousePoint[1]
        clampedDiff = min(self.diameter, max(-self.diameter, verticalDiff))
        dialAngle = ((clampedDiff + self.diameter) / (abs(2*self.diameter) + 1e-9)) *-360
        # update dial GUI angle
        canvas.itemconfig(self.arc, extent=dialAngle)
        # calculate current value of ADSR dial given GUI angle
        minDialValue = dialValues[self.name]['min']
        maxDialValue = dialValues[self.name]['max']

        if self.isADSR:
            dialValues[self.name]['curr'] = minDialValue + (maxDialValue - minDialValue) * abs(dialAngle/360)**self.ratioRamp
            canvas.itemconfig(self.text, text=f'{self.label}{dialValues[self.name]['curr']:.2f}{self.units}')

        else:
            updatedValue = minDialValue + (maxDialValue - minDialValue) * abs(dialAngle/360)**self.ratioRamp
            setattr(self.sourceObj, self.parameter, updatedValue)
            canvas.itemconfig(self.text, text=f'{self.label}{getattr(self.sourceObj,self.parameter):.2f}{self.units}')

            if "delay" in self.name:
                self.sourceObj.delayTimeChanged(updatedValue)

    def destroy(self):
        canvas.delete(self.bg)
        canvas.delete(self.arc)
        canvas.delete(self.text)

    def getStartExtent(self):

        if self.isADSR:
            currVal = dialValues[self.name]['curr']
        else:
            currVal = getattr(self.sourceObj,self.parameter)
        return -360 * ((currVal-self.minValue) / (self.maxValue-self.minValue))**(1/self.ratioRamp)
        # return -360 * ((currVal-self.minValue) / (self.maxValue-self.minValue))**(1/self.ratioRamp)

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
        print(f'{elementName=}')
        self.activeWidget = self.widgets[elementName]
        self.clickPoint = self.mousePoint

        if self.activeWidget.name in sliderValues:
            self.widgets[self.activeWidget.name].update(self.clickPoint, self.mousePoint)

    def mouseSecondaryPressed(self, event):
        removePopup()

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

        if waveType == "sine":
            signal = np.sin(phases)
        elif waveType == "square":
            signal = np.sign(np.sin(phases)) * params.squareAudioDamp
        elif waveType == "saw":
            signal = (2 * ((phases / (2 * np.pi)) % 1) - 1) * params.sawAudioDamp
        signal *= amplitudes

        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)

        return signal

class Effect:
    def __init__(self, effectType: str, slot: int):
        self.effectType = effectType
        self.slot = slot
        self.rectCorners = params.effectRectPositions[slot]
        self.XCorners = params.effectXPositions[slot]
        self.canvasObjects = []
        self.widgetObjects = []
        self.topLeftX = params.effectRectPositions[slot][0]
        self.topLeftY = params.effectRectPositions[slot][1]

        self.buildRectangle()
        self.buildX()
        self.drawTitle()

    
    def buildDial(self, name, centerX, centerY, diameter, minValue, maxValue, sourceObj, parameter, label="", units="", isADSR=False):
        self.addDialToValues(name, minValue, maxValue, centerX, centerY)
        dial = Dial(centerX, centerY, diameter, minValue, maxValue, name, label, units, isADSR, sourceObj, parameter)
        widgets[name] = dial
        sourceObj.widgetObjects.append(dial)

    def buildRectangle(self):
        panelObj = canvas.create_rectangle(self.rectCorners, fill=params.primaryToneDark)
        self.canvasObjects.append(panelObj)

    def buildX(self):
        x_bgObj = canvas.create_rectangle(self.XCorners, fill=params.secondaryToneLight, activefill="white", outline=params.secondaryToneDark, width=1.5)
        x_txtObj = canvas.create_text((self.XCorners[0]+self.XCorners[2])/2, (self.XCorners[1]+self.XCorners[3])/2, text="x", fill=params.primaryToneLight,  font=("Terminal", 14))
        self.canvasObjects.append(x_bgObj)
        self.canvasObjects.append(x_txtObj)

        # add color change on mouse-over
        canvas.tag_bind(x_txtObj, "<Enter>", lambda event, obj=x_bgObj, color="white": colorChange(event, obj, color))
        canvas.tag_bind(x_txtObj, "<Leave>", lambda event, obj=x_bgObj, color=params.secondaryToneLight: colorChange(event, obj, color))
        # add destroyTag to both bg and txt objects
        canvas.tag_bind(x_bgObj, "<Button-1>", self.destroy)
        canvas.tag_bind(x_txtObj, "<Button-1>", self.destroy)

    def drawTitle(self):
        topPad = 10
        titleTxt = canvas.create_text(self.topLeftX+(params.panelWidth/2), self.topLeftY+topPad, text=self.effectType, font=("Terminal", 12, 'bold'), fill=params.primaryToneLight)
        self.canvasObjects.append(titleTxt)

    def destroy(self, event):
        for canvasItem in self.canvasObjects:
            canvas.delete(canvasItem)
        for widgetItem in self.widgetObjects:
            widgetItem.destroy()
        effectObjs[self.slot] = None

        if self.dropdown:
            self.dropdown.removeDropdown()

        #removePopup()
        # canvas.tag_bind(txtObj, "<Enter>", lambda event, obj=txtObj: onPopupTextEnter(event, obj))
        # canvas.tag_bind(txtObj, "<Leave>", lambda event, obj=txtObj: onPopupTextLeave(event, obj))
    def addDialToValues(self, key, minValue, maxValue, centerX, centerY):
        dialValues[key] = {
            'curr': 0,
            'min': minValue,
            'max': maxValue,
            'centerX': centerX,
            'centerY': centerY,
        }
    
class Distortion(Effect):
    def __init__(self, slot):
        self.type = None
        self.overdrive = 0
        self.mix = 0.5
        super().__init__(effectType="distortion", slot=slot)
        super().buildDial(
            name = f"distortion{self.slot}Overdrive", 
            centerX = self.topLeftX + params.panelWidth / 2,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 0,
            maxValue = 2,
            sourceObj = self,
            parameter = "overdrive",
            label="drive "
        )
        dryWetPad = {'x': 83, 'y': 10}
        super().buildDial(
            name = f"distortion{self.slot}DryWet", 
            centerX = self.topLeftX + params.panelWidth / 2 + dryWetPad['x'],
            centerY = self.topLeftY + params.panelHeight / 8  + dryWetPad['y'],
            diameter = 20,
            minValue = 0,
            maxValue = 1,
            sourceObj = self,
            parameter = "mix"
        )

        self.createDropdownListener()
 
    def process(self, signal, frames):
        signal = signal * (1 + self.overdrive * self.mix)
        dry = signal * (1-self.mix)
        if self.type == None:
            wet = 0
        if self.type == "soft clip":
            wet = np.tanh(signal) * self.mix
        elif self.type == "hard clip":
            threshold = 0.2
            wet = np.clip(signal, -threshold, threshold) * self.mix
        elif self.type == "half wave":
            wet = np.maximum(0, signal) * self.mix
        return (dry + wet) 


    def createDropdownListener(self):
        xPad = 10
        yPad = 30
        distortionOptions = ["soft clip", "hard clip", "half wave"]
        typeText = canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad, text="type", font=('Terminal', 10, 'bold', 'underline'), anchor ="w", fill=params.primaryToneLight, activefill="white")
        #canvas.tag_bind(typeText, "<Button-1>", lambda event, options=distortionOptions: self.dropdownCallback(event))
        canvas.tag_bind(typeText, "<Button-1>", lambda event, options=distortionOptions: self.initDropdown(event, options))

        self.currentTypeText = canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad + 20, text="None", font=('Terminal', 7),anchor="w", fill=params.primaryToneLight)
        self.canvasObjects.append(typeText)
        self.canvasObjects.append(self.currentTypeText)      

    def initDropdown(self, event, options):
        # create dropdown and remember it in case of removal through "X" button
        self.dropdown = Dropdown(event.x, event.y, options, self.slot, "effect", self.onSelectDistortionType)

    def onSelectDistortionType(self,event, selectedOption, slot, sourceObj):
        self.type = selectedOption
        canvas.itemconfig(self.currentTypeText, text=f'{self.type}')
        sourceObj.removeDropdown()

class Delay(Effect):
    def __init__(self, slot):
        self.time = 0.5
        self.feedback = 0
        self.mix = 0.5

        self.delaySamples = int(params.samplerate * self.time)
        self.delayBuffer = np.zeros(self.delaySamples)
        self.delayIdx = 0
        super().__init__(slot)
        super().drawTitle("delay")
        self.createTimeDial()
        self.createFeedbackDial()
        self.createDryWetDial()
    #def process(self, signal)

    def process(self, signal, frames):

        startReadIdx = (self.delayIdx - self.delaySamples) % self.delaySamples
        endReadIdx  = startReadIdx + frames
        startWriteIdx = self.delayIdx
        endWriteIdx = startWriteIdx + frames

        # read delay signal from past point in buffer
        if endReadIdx <= self.delaySamples:
            # block will fit without wrapping
            delaySignal = self.delayBuffer[startReadIdx:endReadIdx]
        else:
            # will wrap; need to split into 2 parts
            endPart = self.delayBuffer[startReadIdx:]
            samplesFromStart = endReadIdx - self.delaySamples
            startPart = self.delayBuffer[:samplesFromStart]
            delaySignal = np.concatenate((endPart, startPart))

        if len(delaySignal) > frames:
            delaySignal = delaySignal[:frames] # force shape to be the same

        writeSignal = signal + (delaySignal * self.feedback)
        signal = signal + (delaySignal * self.mix)

        # write delay signal to current point in buffer
        if endWriteIdx <= self.delaySamples:
            self.delayBuffer[startWriteIdx:endWriteIdx] = writeSignal.copy()
        else:
            samplesToEnd = self.delaySamples - startWriteIdx
            self.delayBuffer[startWriteIdx:] = writeSignal[:samplesToEnd]
            samplesFromStart = frames - samplesToEnd
            self.delayBuffer[:samplesFromStart] = writeSignal[samplesToEnd:]

        self.delayIdx = endWriteIdx % self.delaySamples
        return signal
    
    def delayTimeChanged(self, updatedTime):
        print(f'in delay time changed... {updatedTime=}')
        self.delaySamples = int(params.samplerate * updatedTime)
        self.delayBuffer = np.zeros(self.delaySamples)
        self.delayIdx = 0

    def createTimeDial(self):
        dialCenterX = (self.topLeftX + (params.panelWidth /3))
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2)
        dialDiameter = 30
        minDelayTime = 0
        maxDelayTime = 2

        dialName = f"delay{self.slot}Time"
        super().addDialToValues(dialName, minDelayTime, maxDelayTime, dialCenterX, dialCenterY)

        #print(f"again {dialCenterY=}")
        #def __init__(self, centerX, centerY, diameter, minValue, maxValue, name, units, isADSR):

        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minDelayTime, maxDelayTime, dialName, label="time ", units="s", isADSR=False, sourceObj=self, parameter="time")

        widgets[dialName] = dial
        print(f'start extent= {self.mix*360}')

        self.widgetObjects.append(dial)

    def createFeedbackDial(self):
        print(f'{self.topLeftX=}')
        print(f'{self.topLeftY=}')
        dialCenterX = (self.topLeftX + (params.panelWidth *2/3))
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2)
        print(f'{dialCenterX=}')
        print(f'{dialCenterY=}')
        dialDiameter = 30
        minFeedbackValue = 0
        maxFeedbackValue = 1

        dialName = f"delay{self.slot}Feedback"
        super().addDialToValues(dialName, minFeedbackValue, maxFeedbackValue, dialCenterX, dialCenterY)

        #print(f"again {dialCenterY=}")
        #def __init__(self, centerX, centerY, diameter, minValue, maxValue, name, units, isADSR):

        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minFeedbackValue, maxFeedbackValue, dialName, label="feedback ", units="", isADSR=False, sourceObj=self, parameter="feedback")

        widgets[dialName] = dial
        print(f'start extent= {self.mix*360}')
        self.widgetObjects.append(dial)

    def createDryWetDial(self):
        print(f'{self.topLeftX=}{self.topLeftY=}')
        xPad = 83
        yPad = 10
        dialCenterX = (self.topLeftX + (params.panelWidth / 2) + xPad)
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2 + yPad)
        dialDiameter = 20
        dialName = f"delay{self.slot}DryWet"
        minDryWet = 0
        maxDryWet = 1
        self.addDialToValues(dialName, minDryWet, maxDryWet, dialCenterX, dialCenterY)
        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minDryWet, maxDryWet, dialName, label="mix ", units="", isADSR=False, sourceObj=self, parameter="mix")
        widgets[dialName] = dial
        self.widgetObjects.append(dial)
        
class Compressor(Effect):
    def __init__(self, slot):
        self.ratio = 1
        self.threshold = -4
        self.attack = 0.5
        super().__init__(slot)
        super().drawTitle("compressor")
        self.createRatioDial()
        self.createThresholdDial()
        self.createAttackDial()
            
    def process(self, signal, frames):
        return signal
    
    def createAttackDial(self):
        dialCenterX = (self.topLeftX + (params.panelWidth *1/4))
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2)
        dialDiameter = 30
        minAttackValue = 1e-9 
        maxAttackValue = 5
        dialName = f"compressor{self.slot}Attack"
        self.addDialToValues(dialName, minAttackValue, maxAttackValue, dialCenterX, dialCenterY)
        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minAttackValue, maxAttackValue, dialName, label="attack ", units="", isADSR=False, sourceObj=self, parameter="attack")
        dial.ratioRamp = 1
        widgets[dialName] = dial
        self.widgetObjects.append(dial)

    def createThresholdDial(self):
        dialCenterX = (self.topLeftX + (params.panelWidth *2/4))
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2)
        dialDiameter = 30
        minThresholdValue = -10
        maxThresholdValue = 0
        dialName = f"compressor{self.slot}Threshold"
        super().addDialToValues(dialName, minThresholdValue, maxThresholdValue, dialCenterX, dialCenterY)

        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minThresholdValue, maxThresholdValue, dialName, label="thresh ", units="", isADSR=False, sourceObj=self, parameter="threshold")
        dial.ratioRamp = 1
        widgets[dialName] = dial
        self.widgetObjects.append(dial)

    def createRatioDial(self):
        dialCenterX = (self.topLeftX + (params.panelWidth *3/4))
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2)
        dialDiameter = 30
        minRatioValue = 1 
        maxRatioValue = 20

        dialName = f"compressor{self.slot}Ratio"
        self.addDialToValues(dialName, minRatioValue, maxRatioValue, dialCenterX, dialCenterY)
        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minRatioValue, maxRatioValue, dialName, label="ratio ", units="", isADSR=False, sourceObj=self, parameter="ratio")
        dial.ratioRamp = 2
        widgets[dialName] = dial
        self.widgetObjects.append(dial)

    def addDialToValues(self, key, minValue, maxValue, centerX, centerY):
        dialValues[key] = {
            'curr': 0,
            'min': minValue,
            'max': maxValue,
            'centerX': centerX,
            'centerY': centerY
        }


class Filter(Effect):
    def __init__(self, slot):
        self.mix = 0.5
        self.cutoff = 1000
        self.prevFilteredSample = 0
        self.type = "low-pass"

        super().__init__(slot)
        super().drawTitle("filter")
        self.createDryWetDial()
        self.createCutoffDial()
        self.createFilterTypeDropdown()

    def process(self, signal, frames):
        secondsPerSample = 1 / params.samplerate 
        timeConstant = 1 / (2 * np.pi * self.cutoff)
        smoothingFactor = secondsPerSample / (secondsPerSample + timeConstant) 

        filteredSignal = np.zeros(frames)
        filteredSignal[0] = self.prevFilteredSample + smoothingFactor  * (signal[0] - self.prevFilteredSample) 

        for i in range(1, len(signal)):
            filteredSignal[i] = filteredSignal[i-1] + (signal[i]-filteredSignal[i-1])*smoothingFactor

        self.prevFilteredSample = filteredSignal[-1]

        dry = signal * (1-self.mix)
        if self.type == "low-pass":
            wet = filteredSignal * self.mix

        elif self.type == "high-pass":
            wet = (signal-filteredSignal) * self.mix
        else:
            print('unrecognized filter type')
            wet = signal*self.mix

        return dry+wet

    def createFilterTypeDropdown(self):
        xPad = 10
        yPad = 30
        typeText = canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad, text="type", font=('Terminal', 10, 'bold', 'underline'), anchor ="w", fill=params.primaryToneLight, activefill="white")
        self.currentTypeText = canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad + 20, text="None", font=('Terminal', 7),anchor="w", fill=params.primaryToneLight)
        canvas.tag_bind(typeText, "<Button-1>", lambda event: createPopup(event.x, event.y, "filter", self.slot, sourceObj=self))

        self.canvasObjects.append(typeText)
        self.canvasObjects.append(self.currentTypeText)      

    def onSelectFilterType(self, event, selectedType):
        removePopup()
        self.type = selectedType
        canvas.itemconfig(self.currentTypeText, text=f'{self.type}')
        print(f"Filter type is {self.type} in {self.slot}")


    def createCutoffDial(self):
        dialCenterX = (self.topLeftX + (params.panelWidth *1/2))
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2)
        dialDiameter = 30
        minCutoffValue = 0.01
        maxCutoffValue = 20_000

        dialName = f"filter{self.slot}Cutoff"
        self.addDialToValues(dialName, minCutoffValue, maxCutoffValue, dialCenterX, dialCenterY)
        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minCutoffValue, maxCutoffValue, dialName, label="cutoff ", units="", isADSR=False, sourceObj=self, parameter="cutoff")
        dial.ratioRamp = 4
        widgets[dialName] = dial
        self.widgetObjects.append(dial)
        # dialDiameter = 30
        # minFeedbackValue = 0
        # maxFeedbackValue = 1

        # dialName = f"delay{self.slot}Feedback"
        # self.addDialToValues(dialName, minFeedbackValue, maxFeedbackValue, dialCenterX, dialCenterY)

        # #print(f"again {dialCenterY=}")
        # #def __init__(self, centerX, centerY, diameter, minValue, maxValue, name, units, isADSR):

        # dial = Dial(dialCenterX, dialCenterY, dialDiameter, minFeedbackValue, maxFeedbackValue, dialName, label="feedback ", units="", isADSR=False, sourceObj=self, parameter="feedback")

        # widgets[dialName] = dial
        # print(f'start extent= {self.mix*360}')
        # self.widgetObjects.append(dial)









    def createDryWetDial(self):
        print(f'{self.topLeftX=}{self.topLeftY=}')
        xPad = 83
        yPad = 10
        dialCenterX = (self.topLeftX + (params.panelWidth / 2) + xPad)
        dialCenterY = (self.topLeftY + (params.panelHeight/4) / 2 + yPad)
        dialDiameter = 20
        dialName = f"filter{self.slot}DryWet"
        minDryWet = 0
        maxDryWet = 1
        self.addDialToValues(dialName, minDryWet, maxDryWet, dialCenterX, dialCenterY)
        dial = Dial(dialCenterX, dialCenterY, dialDiameter, minDryWet, maxDryWet, dialName, label="mix ", units="", isADSR=False, sourceObj=self, parameter="mix")
        widgets[dialName] = dial
        self.widgetObjects.append(dial)

    # probaly but this function into parent
    def addDialToValues(self, key, minValue, maxValue, centerX, centerY):
        dialValues[key] = {
            'curr': 0,
            'min': minValue,
            'max': maxValue,
            'centerX': centerX,
            'centerY': centerY
        }

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