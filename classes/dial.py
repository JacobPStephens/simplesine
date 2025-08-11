import params

class Dial:
    def __init__(self, centerX, centerY, diameter, minValue, maxValue, name, label, units, isADSR, canvas, state, sourceObj=None, parameter=None, ratioRamp=1):
        self.centerX = centerX
        self.centerY = centerY
        self.diameter = diameter
        self.minValue = minValue
        self.maxValue = maxValue
        self.name = name
        self.label = label
        self.units = units
        self.isADSR = isADSR
        self.ratioRamp = ratioRamp
        self.sourceObj = sourceObj
        self.parameter = parameter

        self.canvas = canvas
        self.state = state
        self.createDial()

    def createDial(self):
        if self.isADSR:
            textPadding = params.textPaddingADSR
        else:
            textPadding = params.textPaddingSmall
        startExtent = self.getStartExtent()
        tagName = f'{self.name}_tag'
        dialCoords = [self.centerX-(self.diameter/2), self.centerY-(self.diameter/2), self.centerX+(self.diameter/2), self.centerY+(self.diameter/2)]
        self.bg = self.canvas.create_oval(dialCoords, fill=params.primaryToneDark, outline="black", width=1.5, tags=tagName)
        self.arc = self.canvas.create_arc(dialCoords, fill=params.primaryToneLight, start= 270, extent= startExtent, tags=tagName)
        if self.isADSR:
            self.text = self.canvas.create_text(self.centerX,self.centerY+(self.diameter/2)+textPadding, text=f"{self.state.dialValues[self.name]['curr']:.2f}{self.units}", fill="white")
        else:
            self.text = self.canvas.create_text(self.centerX,self.centerY+(self.diameter/2)+textPadding, text=f"{self.label}{self.state.dialValues[self.name]['curr']:.2f}{self.units}", font=("TKDefaultFont", 6), fill="white")
        self.canvas.tag_bind(tagName, "<Button-1>", lambda event: self.state.inputObj.mouseClicked(event, self.name))       


    def update(self, clickPoint, mousePoint):
        # calculate dial angle using user's mouse location
        verticalDiff = clickPoint[1] - mousePoint[1]
        clampedDiff = min(self.diameter, max(-self.diameter, verticalDiff))
        dialAngle = ((clampedDiff + self.diameter) / (abs(2*self.diameter) + 1e-9)) *-360
        # update dial GUI angle
        self.canvas.itemconfig(self.arc, extent=dialAngle)
        # calculate current value of ADSR dial given GUI angle
        minDialValue = self.state.dialValues[self.name]['min']
        maxDialValue = self.state.dialValues[self.name]['max']

        if self.isADSR:
            self.state.dialValues[self.name]['curr'] = minDialValue + (maxDialValue - minDialValue) * abs(dialAngle/360)**self.ratioRamp
            self.canvas.itemconfig(self.text, text=f'{self.label}{self.state.dialValues[self.name]['curr']:.2f}{self.units}')

        else:
            updatedValue = minDialValue + (maxDialValue - minDialValue) * abs(dialAngle/360)**self.ratioRamp
            setattr(self.sourceObj, self.parameter, updatedValue)
            self.canvas.itemconfig(self.text, text=f'{self.label}{getattr(self.sourceObj,self.parameter):.2f}{self.units}')

            if "delay" in self.name:
                self.sourceObj.delayTimeChanged(updatedValue)

    def destroy(self):
        self.canvas.delete(self.bg)
        self.canvas.delete(self.arc)
        self.canvas.delete(self.text)

    def getStartExtent(self):

        if self.isADSR:
            currVal = self.state.dialValues[self.name]['curr']
        else:
            currVal = getattr(self.sourceObj,self.parameter)
        return -360 * ((currVal-self.minValue) / (self.maxValue-self.minValue))**(1/self.ratioRamp)
        # return -360 * ((currVal-self.minValue) / (self.maxValue-self.minValue))**(1/self.ratioRamp)