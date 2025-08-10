import params
import numpy as np
from .effect import Effect

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
        super().createDryWetDial()
       
        options = ["soft clip", "hard clip", "half wave"]
        super().createDropdownListener(self, options)

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
