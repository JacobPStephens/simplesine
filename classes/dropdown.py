import params, utils

class Dropdown:

    def __init__(self, x: int, y: int, options: list[str], slot: int, panelType: str, callback: callable, canvas, state):
        self.options = options
        self.objects = []
        self.canvas = canvas
        self.state = state
        self.removeExistingDropdowns()
        self.createDropdown(x, y, slot, panelType, callback)
        state.dropdowns.append(self)

    def createDropdown(self, x, y, slot, panelType, callback):
        popupWidth = 80
        topPadding = 12
        elementHeight = 25

        for i, option in enumerate(self.options):
            #piece = canvas.create_rectangle(x-(popupWidth/2), y+(delta_y*i), x+(popupWidth/2), y+(delta_y*(i+1)), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
            piece = self.canvas.create_rectangle(x-popupWidth/2, y+elementHeight*i, x+popupWidth/2, y+elementHeight*(i+1), fill=params.primaryToneDark, activefill=params.primaryToneLight, outline="black")
            textObj = self.canvas.create_text(x, y+elementHeight*i+topPadding,text=option, font=("Terminal", 9), fill="white")
            #textObj = canvas.create_text(x, y+(delta_y*i)+padFromTop,text=effectText, font=("Terminal", 9), fill="white")
            self.canvas.tag_bind(piece, "<Button-1>", lambda event, optionName=option, slotArg=slot: callback(event, optionName, slotArg, self))
            self.canvas.tag_bind(textObj, "<Button-1>", lambda event, optionName=option, slotArg=slot: callback(event, optionName, slotArg, self))

            self.canvas.tag_bind(textObj, "<Enter>", lambda event, obj=piece, color=params.primaryToneLight: utils.colorChange(event, self.canvas, obj, color))
            self.canvas.tag_bind(textObj, "<Leave>", lambda event, obj=piece, color=params.primaryToneDark: utils.colorChange(event, self.canvas, obj, color))

            self.objects.append(piece)
            self.objects.append(textObj)        

    def removeDropdown(self):
        for obj in self.objects:
            self.canvas.delete(obj)
        self.objects = []
        print('delted popup line 286s')
    
    def removeExistingDropdowns(self):
        for dropdown in self.state.dropdowns:
            dropdown.removeDropdown()
        self.state.dropdowns = []