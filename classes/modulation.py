import params
from .panel_component import PanelComponent
class Modulation(PanelComponent):
    def __init__(self, title, slot, canvas, state):
        self.canvas = canvas
        super().__init__(title, slot, canvas, state)

    def createParamListener(self):
        xPad = 140
        yPad = 40
        paramText = self.canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad, text="param", font=('Terminal', 10, 'bold', 'underline'), anchor ="w", fill=params.primaryToneLight, activefill="white")
        #canvas.tag_bind(typeText, "<Button-1>", lambda event, options=options: self.initDropdown(event, options))

        self.currentParamText = self.canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad + 20, text="None", font=('Terminal', 7),anchor="w", fill=params.primaryToneLight)
        self.canvasObjects.append(paramText)
        self.canvasObjects.append(self.currentParamText) 