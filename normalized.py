import time
from pysinewave import SineWave

# sines     = [0.7,     0.55,   0.8]
# normals   = [0.7/2.05 0.55/2.05, 0.8/2.05]
#           = [0.341,   0.268   0.390]



# sines = [0.5]
# normalize = [1]



rawAmps = dict()
normalizedAmps = dict()


def normalize():

    totalRawAmps = sum(rawAmps.values()) + 1

    for s in rawAmps:
        normalizedAmps[s] = (rawAmps[s] / totalRawAmps)
        s.sinewave_generator.amplitude = (rawAmps[s] / totalRawAmps)

def main():


    sine1 = SineWave(pitch=0, decibels=0, decibels_per_second=1)
    sine1.sinewave_generator.amplitude = 0.7
    rawAmps[sine1] = sine1.sinewave_generator.amplitude

    sine2 = SineWave(pitch=3, decibels=0, decibels_per_second=1)
    sine2.sinewave_generator.amplitude = 1.0
    rawAmps[sine2] = sine2.sinewave_generator.amplitude

    sine3 = SineWave(pitch=7, decibels=0, decibels_per_second=1)
    sine3.sinewave_generator.amplitude = 0.8
    rawAmps[sine3] = sine3.sinewave_generator.amplitude

    print(f'{rawAmps=}')
    normalize()
    print(f'{normalizedAmps=}')

    sine1.play()
    sine2.play()
    sine3.play()

    time.sleep(5)

    sine1.stop()
    sine2.stop()
    sine3.stop()

main()