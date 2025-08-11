import params
import numpy as np
from .effect import Effect

class Filter(Effect):
    def __init__(self, slot, canvas, state):
        self.mix = 0.5
        self.cutoff = 1000
        self.prevFilteredSample = 0
        self.type = "low-pass"

        super().__init__("filter", slot, canvas, state)
        super().buildDial(
            name = f"filter{self.slot}Cutoff", 
            centerX = self.topLeftX + params.panelWidth / 2,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 1e-9,
            maxValue = 10_000,
            sourceObj = self,
            parameter = "cutoff",
            label="cutoff ",
            ratioRamp = 4
        )
        super().createDryWetDial()

        options = ["low-pass", "high-pass"]
        super().createDropdownListener(options)
        #self.createDropdownListener()

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