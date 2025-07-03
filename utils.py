import math
def decibelsToAmplitude(decibels):
    return 2**(decibels / 10)

def amplitudeToDecibels(amplitude):
    if amplitude == 0:
        return -999
    return 20 * math.log(amplitude, 10)
