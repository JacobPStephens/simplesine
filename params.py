import utils


# attack: the time from note press to peak volume
# decay: the time from peak volume to susain volume
# sustain: the volume while note is held, expressed as percent of peak volume
# release: the time from sustain volume to silence

# tmp delay variables for testing
delayTime = 0.5

# volume
volume = 1.0
peakVolume = utils.decibelsToAmplitude(0)
maxVolume = utils.decibelsToAmplitude(0)
minVolume = 1e-9
masterDamp = 0.3
squareAudioDamp = 0.3
sawAudioDamp = 0.3

# visual
waveVisualIncrease = {
    "sine": 55,
    "square" : 150,
    "saw": 150,
}
visualShrink = 0.2


# pitch
freq = 0
minFreq = -200
maxFreq = 200

# Attack
defaultAttack = 0.25
minAttack = 0.1
maxAttack = 5
# Decay
defaultDecay = 0.5
minDecay = 0.1
maxDecay = 5
# Sustain
defaultSustain = 3/4
minSustain = 0
maxSustain = 1
# Release
defaultRelease = 1
minRelease = 0.1
maxRelease = 5

# Sound stream settings
blocksize = 512 # default = 0
samplerate = 44100

# Compressor
smoothedGain = 0
alphaAttack = 0.01 # this is causing the crackle
alphaRelease = 0.01
ratioCurve = 1.3

# GUI Colors
primaryToneLight = "#50ACC0"
primaryToneDark = "#1E393F"
secondaryToneLight = "#2B2B2B"
secondaryToneDark = "#1E1E1E"

textPaddingADSR = 10
textPaddingSmall = 8
dialHeight = 60
dialWidth = 60
dialCenter_y = 260
dialCenters_x = {
    "attack":260,
    "decay":353.33,
    "sustain":446.66,
    "release":540
}

sliders = {
    "volume": {
        "left": dialCenters_x["attack"],
        "right": dialCenters_x["decay"],
        "center": dialCenters_x["decay"] - dialCenters_x["attack"],
        "yPos": 190,
        "height": 3,
        "knobWidth": 10,
        "knobHeight": 10
        
    },
    "frequency": {
        "left": dialCenters_x["sustain"],
        "right": dialCenters_x["release"],
        "center": dialCenters_x["release"] - dialCenters_x["sustain"],
        "yPos": 190,
        "height": 3,
        "knobWidth": 10,
        "knobHeight": 10
        
    }

}

# same code as main.py
panelHeight = 305
panelWidth = 200
xWidth = 30
effectRectPositions = {}
effectXPositions = {}
panelLineHeight = 3
rightPad = 2
for i in range(0,4):
    y = (panelHeight/4*i) + 10 + panelLineHeight
    y2 = (panelHeight/4*(i+1)) + 10
    effectRectPositions[i] = [590, y, 790, y2]
    effectXPositions[i] = [790-xWidth, y, 790-rightPad, y+xWidth]
    #panel = canvas.create_rectangle(10, y+panelLineHeight, 210, y2+panelLineHeight, fill=params.secondaryToneLight, activefill=params.primaryToneDark, tags=tagName)

# make bottom panel a bit shorter
effectRectPositions[3][3] -= panelLineHeight
effectXPositions[3][3] -= 1



xWidth = 30
# effectXPositions = {
#     0: [790-xWidth, 10, 790, 10+xWidth],
#     1: [],
#     2: [],
#     3: [],
# }



noteCeiling = 88
defaultLowestNote = 48

# sine visuals
sineWidth = 4