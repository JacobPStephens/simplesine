import tkinter as tk
import params
# import threading
import utils
#from midi import midiListener

import inputs
from simplesine import notePlayed, noteReleased
# import Dial
# import MouseInfo

class GUI:

    def __init__(self):
        self.root = None
        self.canvas = None
        self.keysGUI = []

    def buildWindow(self): # returns root
        self.root = tk.Tk()    
        self.root.geometry("800x405+100+50")
        self.root.resizable(False, False)
        self.root.title("simplesine")
        self.root.bind("<KeyPress>", inputs.onKeyPressed) # maybe do these in simplesine
        self.root.bind("<KeyRelease>", inputs.onKeyReleased)
        self.root.mainloop()

        return self.root #?
    
    def buildCanvas(self):
        self.canvas = tk.Canvas(self.root, width=800,height=405, bg="#2B2B2B")
        self.buildBorder()
        self.buildPanels()
        self.canvas.pack()

        return self.canvas

    def buildBorder(self):
        # build 4 sides of window border
        self.canvas.create_rectangle(0, 0, 800, 10, fill=params.primaryToneLight)
        self.canvas.create_rectangle(0, 395, 800, 405, fill=params.primaryToneLight)
        self.canvas.create_rectangle(0, 10, 10, 395, fill=params.primaryToneLight)
        self.canvas.create_rectangle(790, 10, 800, 395, fill=params.primaryToneLight)

    def buildPanels(self):
        bgMid = self.canvas.create_rectangle(210, 10, 590, 395, fill=params.secondaryToneDark, outline=None)
        effectsTxt = self.canvas.create_text(690, 30, text="effects", justify='center', font=("Terminal", 16, 'bold'), fill=params.secondaryToneDark)
        modulationsTxt = self.canvas.create_text(110, 30, text="modulations", justify='center', font=("Terminal", 16, 'bold'), fill=params.secondaryToneDark)
        centerTitle = self.canvas.create_text(400, 40, text="simplesine", justify='center', font=("Terminal", 30, 'bold'), fill=params.primaryToneLight)
        
        panelHeight = 305 # total height - 2 * border - keysHeight
        leftPanelLines = []
        rightPanelLines = []
        panelLineHeight = 3
        for i in range(1,4):
            y = (panelHeight/4*i) + 10
            leftPanelLines.append(self.canvas.create_rectangle(10, y, 210, y+panelLineHeight, fill=params.secondaryToneDark))
            rightPanelLines.append(self.canvas.create_rectangle(590, y, 790, y+panelLineHeight, fill=params.secondaryToneDark))

    def buildKeys(self):
        leftx = 10
        whiteKeyWidth = 52.0 # (800 - 10 - 10) / 15 (#keys)
        whiteKeyHeight = 80
        heightOffset = 30
        blackKeyWidth = 20
        blackKeyHeight = 50
        keyTexts = []

        for i in range(29):
            if i in [5, 13, 19, 27]:
                self.keysGUI.append(0)
                keyTexts.append(0)
            elif (i % 2 == 0):
                tmp = self.canvas.create_rectangle(leftx, 395-whiteKeyHeight, leftx+whiteKeyWidth, 395, fill=params.primaryToneDark, outline="white")
                keyTexts.append(self.canvas.create_text(leftx+(whiteKeyWidth/2), 395-(whiteKeyHeight * 1 / 4), text=utils.keyboardKeys[i], font=("Terminal", 9), fill="#CCCCCC"))

                self.keysGUI.append(tmp)
                leftx += whiteKeyWidth
            else:
                tmp = self.canvas.create_rectangle(leftx-(blackKeyWidth/2), 395-blackKeyHeight-heightOffset, leftx+blackKeyWidth-(blackKeyWidth/2), 395-heightOffset,fill=params.primaryToneLight,outline="white")
                keyTexts.append(self.canvas.create_text(leftx, 395-(blackKeyHeight), text=utils.keyboardKeys[i], font=("Terminal", 9), fill='white'))
                self.keysGUI.append(tmp)

        # lift all black keys to front of canvas
        for i in range(len(self.keysGUI)):
            if self.keysGUI[i] and (i % 2 == 1):
                self.canvas.lift(keysGUI[i])
                self.canvas.lift(keyTexts[i])
                
    
        # remove dummy 0s from keyGUI list
        numRemoved = 0
        for i in [5, 13, 19, 27]:
            self.keysGUI.pop(i-numRemoved)
            numRemoved += 1
        
        return self.keysGUI

    def buildWidgets(self):
        widgets = {}

        # ADSR knobs
        for name in ['attack', 'decay', 'sustain', 'release']:
            widgets[name] = Dial(name, self.canvas)

        #widgets['volume'] = Slider()


        return widgets



    # def buildDials(self):
    #     dials = {}
    #     for stage in ['attack', 'decay', 'sustain', 'release']:
    #         dials[stage] = Dial(stage)
    #     return dials



# def buildGUI():
#     global root, canvas, dials, keysGUI

    
#     dials = {}
#     keysGUI = []



#     def mainGUI():

#         handleInput()



#     def bindInputToCallbacks():
#         mouse = MouseInfo()
#         root.bind("<Motion>", mouse.mouseMotion)
#         root.bind("<ButtonRelease-1>", mouse.mouseReleased)
        
#         # bind every tag to mouseClicked function with parameter of string of tag that was clicked
#         for tag in allTags:
#             canvas.tag_bind(tag, "<Button-1>", lambda event: mouse.mouseClicked(event, tag))
#         # canvas.tag_bind("attack_tag", "<Button-1>", lambda event: mouse.dialClicked(event, "attack"))
#         # canvas.tag_bind("decay_tag", "<Button-1>", lambda event: mouse.dialClicked(event, "decay"))
#         # canvas.tag_bind("sustain_tag", "<Button-1>", lambda event: mouse.dialClicked(event, "sustain"))
#         # canvas.tag_bind("release_tag", "<Button-1>", lambda event: mouse.dialClicked(event, "release"))
        



    


    

#     mainGUI()


def onKeyPressed(event):
    charToTranposeAmount = {
        ")": 1,
        "(": -1,
        "+": 12,
        "-": -12
    }
    if event.char in charToTranposeAmount:
        amnt = charToTranposeAmount[event.char]
        utils.transpose(amnt)

    if event.char.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
        return
    
    localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.char.lower()]
    globalNote = localNote + simplesine.LOWEST_NOTE
    if globalNote > 88:
        return
    
    simplesine.notePlayed(globalNote)


def onKeyReleased(event):
    if event.keysym.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
        return
    
    localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.keysym.lower()]
    globalNote = localNote + simplesine.LOWEST_NOTE

    with simplesine.lock:
        simplesine.noteReleased(globalNote)


#     # freq = utils.NOTE_TO_FREQ[globalNote]

#     # with lock:
#     #     for note in activeNotes:
#     #         if note.freq == freq and not note.released:
#     #             note.released = True
#     #             highlightNote(globalNote, "note_off")