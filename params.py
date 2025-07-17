import utils

defaultMaxVolume = utils.decibelsToAmplitude(-2)

# Attack
defaultAttack = 1
minAttack = 1e-9
maxAttack = 5
# Decay
defaultDecay = 0.5
minDecay = 1e-9
maxDecay = 5
# Sustain
defaultSustain = defaultMaxVolume * 3/4
minSustain = 0
maxSustain = defaultMaxVolume
# Release
defaultRelease = 1
minRelease = 1e-9
maxRelease = 5

# Sound stream settings
blocksize = 0 # default = 0
samplerate = 44100

# Compressor
smoothedGain = 0
alphaAttack = 0.6
alphaRelease = 0.01
ratioCurve = 1.5

# GUI Colors
primaryToneLight = "#50ACC0"
primaryToneDark = "#1E393F"
secondaryToneLight = "#2B2B2B"
secondaryToneDark = "#1E1E1E"

textPadding = 10
dialHeight = 60
dialWidth = 60
dialCenter_y = 260
dialCenters_x = {
    "attack":260,
    "decay":353.33,
    "sustain":446.66,
    "release":540
}

noteCeiling = 88
defaultLowestNote = 48