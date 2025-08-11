import params
from .panel_component import PanelComponent

class Effect(PanelComponent):
    def __init__(self, effectType: str, slot: int, canvas, state):
        self.effectType = effectType
        self.slot = slot
        super().__init__(effectType, slot, canvas, state)

    def createDryWetDial(self):
        dryWetPad = {'x': 83, 'y': 10}
        super().buildDial(
            name = f"{self.effectType}{self.slot}DryWet", 
            centerX = self.topLeftX + params.panelWidth / 2 + dryWetPad['x'],
            centerY = self.topLeftY + params.panelHeight / 8  + dryWetPad['y'],
            diameter = 20,
            minValue = 0,
            maxValue = 1,
            sourceObj = self,
            parameter = "mix",
            label="mix "
        )