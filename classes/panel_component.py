import params, utils
from .dropdown import Dropdown
from .dial import Dial

class PanelComponent:
    def __init__(self, title, slot, canvas, state):
        self.canvasObjects = []
        self.rectCorners = params.effectRectPositions[slot]
        self.XCorners = params.effectXPositions[slot]
        self.topLeftX = params.effectRectPositions[slot][0]
        self.topLeftY = params.effectRectPositions[slot][1]
        self.widgetObjects = []
        self.dropdown = None
        self.title = title

        self.canvas = canvas
        self.state = state
        self.buildRectangle()
        self.buildX()
        self.drawTitle()

    def buildRectangle(self):
        panelObj = self.canvas.create_rectangle(self.rectCorners, fill=params.primaryToneDark)
        self.canvasObjects.append(panelObj)

    def buildX(self):
        x_bgObj = self.canvas.create_rectangle(self.XCorners, fill=params.secondaryToneLight, activefill="white", outline=params.secondaryToneDark, width=1.5)
        x_txtObj = self.canvas.create_text((self.XCorners[0]+self.XCorners[2])/2, (self.XCorners[1]+self.XCorners[3])/2, text="x", fill=params.primaryToneLight,  font=("Terminal", 14))
        self.canvasObjects.append(x_bgObj)
        self.canvasObjects.append(x_txtObj)

        # add color change on mouse-over
        self.canvas.tag_bind(x_txtObj, "<Enter>", lambda event, obj=x_bgObj, color="white": utils.colorChange(event, self.canvas, obj, color))
        self.canvas.tag_bind(x_txtObj, "<Leave>", lambda event, obj=x_bgObj, color=params.secondaryToneLight: utils.colorChange(event, self.canvas, obj, color))
        # add destroyTag to both bg and txt objects
        self.canvas.tag_bind(x_bgObj, "<Button-1>", self.destroy)
        self.canvas.tag_bind(x_txtObj, "<Button-1>", self.destroy)

    def drawTitle(self):
        topPad = 10
        titleTxt = self.canvas.create_text(self.topLeftX+(params.panelWidth/2), self.topLeftY+topPad, text=self.title, font=("Terminal", 12, 'bold'), fill=params.primaryToneLight)
        self.canvasObjects.append(titleTxt)

    def destroy(self, event):
        for canvasItem in self.canvasObjects:
            self.canvas.delete(canvasItem)
        for widgetItem in self.widgetObjects:
            widgetItem.destroy()
        self.state.effectObjs[self.slot-4] = None

        if self.dropdown:
            self.dropdown.removeDropdown()

    def buildDial(self, name, centerX, centerY, diameter, minValue, maxValue, sourceObj, parameter, label="", units="", isADSR=False, ratioRamp=1):
        self.addDialToValues(name, minValue, maxValue, centerX, centerY)
        dial = Dial(centerX, centerY, diameter, minValue, maxValue, name, label, units, isADSR, self.canvas, self.state, sourceObj, parameter, ratioRamp)
        self.state.widgets[name] = dial
        sourceObj.widgetObjects.append(dial)

    def addDialToValues(self, key, minValue, maxValue, centerX, centerY):
        self.state.dialValues[key] = {
            'curr': 0,
            'min': minValue,
            'max': maxValue,
            'centerX': centerX,
            'centerY': centerY,
        }
    def createDropdownListener(self, options):
        xPad = 10
        yPad = 30
        typeText = self.canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad, text="type", font=('Terminal', 10, 'bold', 'underline'), anchor ="w", fill=params.primaryToneLight, activefill="white")
        self.canvas.tag_bind(typeText, "<Button-1>", lambda event, options=options: self.initDropdown(event, options))

        self.currentTypeText = self.canvas.create_text(self.topLeftX + xPad, self.topLeftY + yPad + 20, text="None", font=('Terminal', 7),anchor="w", fill=params.primaryToneLight)
        self.canvasObjects.append(typeText)
        self.canvasObjects.append(self.currentTypeText)    
    
    def initDropdown(self, event, options):
        # create dropdown and remember it in case of removal through "X" button
        self.dropdown = Dropdown(event.x, event.y, options, self.slot, "effect", self.onSelectOption, self.canvas, self.state)

    def onSelectOption(self,event, selectedOption, slot, sourceObj):
        self.type = selectedOption
        self.canvas.itemconfig(self.currentTypeText, text=f'{self.type}')
        sourceObj.removeDropdown()