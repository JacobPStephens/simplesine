import params
from .modulation import Modulation

class Oscillator(Modulation):
    def __init__(self, slot, canvas, state):
        super().__init__("oscillator", slot, canvas, state)
        self.slot = slot
        self.rate = 50
        self.depth = 0.5
        self.param = None

        super().buildDial(
            name = f"oscillator{self.slot}Rate", 
            centerX = self.topLeftX + params.panelWidth * 1/4,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 1e-9,
            maxValue = 20,
            sourceObj = self,
            parameter = "rate",
            label="rate ",
            units=" Hz",
            ratioRamp = 2
        )

        super().buildDial(
            name = f"oscillator{self.slot}Depth", 
            centerX = self.topLeftX + params.panelWidth * 2/4,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 0,
            maxValue = 1,
            sourceObj = self,
            parameter = "depth",
            label="depth "
        )

        super().createParamListener()