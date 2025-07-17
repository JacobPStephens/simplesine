import params

class Dial:

    def __init__(self, name, canvas):
        self.name = name
        dialWidth = params.dialWidth
        dialHeight = params.dialHeight
        dialCenter_y = params.dialCenter_y
        dialCenters_x = params.dialCenters_x
        textPadding = params.textPadding
        startExtent = 270
        self.bg = canvas.create_oval(dialCenters_x[self.name]-(dialWidth/2), dialCenter_y-(dialHeight/2), dialCenters_x[self.name]+(dialWidth/2), dialCenter_y+(dialHeight/2), fill=params.primaryToneDark, outline="black", width=1.5, tags=f'{self.name}_tag')
        self.arc = canvas.create_arc(dialCenters_x[self.name]-(dialWidth/2), dialCenter_y-(dialHeight/2), dialCenters_x[self.name]+(dialWidth/2), dialCenter_y+(dialHeight/2), fill=params.primaryToneLight, start= startExtent, extent=-359, tags=f'{self.name}_tag')
        self.text = canvas.create_text(dialCenters_x[self.name], dialCenter_y+(dialHeight/2)+textPadding, text=f'{self.name:.2f}s', fill="white")

    def update(self, clickPoint, mousePoint):
        # calculate dial angle using user's mouse location
        verticalDiff = clickPoint[1] - mousePoint[1]
        clampedDiff = min(50, max(-50, verticalDiff))
        dialAngle = ((clampedDiff + 50) / (100 + 1e-9)) *-360
        # update dial GUI angle
        canvas.itemconfig(self.arc, extent=dialAngle)
        # calculate current value of ADSR dial given GUI angle
        minDialValue = dialValues[self.name]['min']
        maxDialValue = dialValues[self.name]['max']
        dialValues[self.name]['curr'] = minDialValue + (maxDialValue - minDialValue) * abs(dialAngle/360)**2
        # update text to match value
        if self.name != "sustain":
            canvas.itemconfig(self.text, text=f'{dialValues[self.name]['curr']:.2f}s')
        else:
            canvas.itemconfig(self.text, text=f'{dialValues[self.name]['curr']:.2f}dB')

