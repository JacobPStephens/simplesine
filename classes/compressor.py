import params
from .effect import Effect

class Compressor(Effect):
    def __init__(self, slot):
        self.ratio = 1
        self.threshold = -4
        self.attack = 0.5
        super().__init__("compressor", slot)

        super().buildDial(
            name = f"compressor{self.slot}Attack", 
            centerX = self.topLeftX + params.panelWidth * 1/4,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 1e-9,
            maxValue = 5,
            sourceObj = self,
            parameter = "attack",
            label="attack "
        )
        super().buildDial(
            name = f"compressor{self.slot}Threshold", 
            centerX = self.topLeftX + params.panelWidth * 2/4,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = -10,
            maxValue = 0,
            sourceObj = self,
            parameter = "threshold",
            label="thresh "
        )
        super().buildDial(
            name = f"compressor{self.slot}Ratio", 
            centerX = self.topLeftX + params.panelWidth * 3/4,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 1,
            maxValue = 20,
            sourceObj = self,
            parameter = "ratio",
            label = "ratio ",
            ratioRamp = 2
        )
                
    def process(self, signal, frames):
        return signal