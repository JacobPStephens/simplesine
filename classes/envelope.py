import params
from .modulation import Modulation


class Envelope(Modulation):
    def __init__(self, slot, canvas, state):
        super().__init__("envelope", slot, canvas, state)
        self.slot = slot
        self.attack = 1
        self.decay = 1
        self.sustain = 1
        self.release = 1
        self.param = None

        xPad = -15
        super().buildDial(
            name = f"envelope{self.slot}Attack", 
            centerX = self.topLeftX + params.panelWidth * 1/6 + xPad,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 20,
            minValue = 1e-9,
            maxValue = 5,
            sourceObj = self,
            parameter = "attack",
            label="A=",
            ratioRamp=2
        )

        super().buildDial(
            name = f"envelope{self.slot}Decay", 
            centerX = self.topLeftX + params.panelWidth * 2/6 + xPad,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 20,
            minValue = 1e-9,
            maxValue = 5,
            sourceObj = self,
            parameter = "decay",
            label="D=",
            ratioRamp=2
        )

        super().buildDial(
            name = f"envelope{self.slot}Sustain", 
            centerX = self.topLeftX + params.panelWidth * 3/6 + xPad,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 20,
            minValue = 1e-9,
            maxValue = 1,
            sourceObj = self,
            parameter = "sustain",
            label="S=",
        )

        super().buildDial(
            name = f"envelope{self.slot}Release", 
            centerX = self.topLeftX + params.panelWidth * 4/6 + xPad,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 20,
            minValue = 1e-9,
            maxValue = 5,
            sourceObj = self,
            parameter = "release",
            label="R=",
            ratioRamp=2
        )

        super().createParamListener()