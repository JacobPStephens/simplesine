import time
import numpy as np
class Limiter:
    def __init__(self, threshold, rate):
        self.gain = 1.0
        self.threshold = threshold
        self.rate = rate # between 0 and 1
        self.p = 0
    def process(self, signal):
        peakAmplitude = np.max(np.abs(signal)) 
        if peakAmplitude > self.threshold and peakAmplitude > 0:
            targetGain = self.threshold / peakAmplitude
        else:
            targetGain = 1.0
        

        c = time.time()
        dt = c - self.p
        self.p = c

        self.gain = targetGain + (self.gain - targetGain) * np.exp(-self.rate * dt)
        print(peakAmplitude, self.gain)
        return signal * self.gain
