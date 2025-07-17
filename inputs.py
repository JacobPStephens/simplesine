import mido, utils
from simplesine import lock, notePlayed, noteReleased, LOWEST_NOTE



class MouseInfo():
    def __init__(self, dials):
        self.mousePoint: tuple[int, int] = None
        self.clickPoint: tuple[int, int] = None
        self.dials = dials
        self.activeDial = None

    def mouseClicked(self, event, stage):
        self.activeDial = self.dials[stage]
        self.clickPoint = self.mousePoint

        return self.activeDial

    def mouseReleased(self, event):
        self.activeDial = None

    def mouseMotion(self, event):
        self.mousePoint = (event.x, event.y)
        if self.activeDial:
            self.dials[self.activeDial.name].update(self.clickPoint, self.mousePoint)

def midiListener():
    if len(mido.get_input_names()) <= 1:
        return
    portName = mido.get_input_names()[1]
    print(f'{portName=}')
    with mido.open_input(portName) as inport:
        print('listening...')
        for msg in inport:
            onMidiAction(msg)

def onMidiAction(msg):
    if not msg.note or msg.note > 108:
        return
    
    # maybe add lock here
    if msg.type == "note_on":
        notePlayed(msg.note)
        
    elif msg.type == "note_off":
        noteReleased(msg.note)


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
    globalNote = localNote + LOWEST_NOTE
    if globalNote > 88:
        return
    notePlayed(globalNote)


def onKeyReleased(event):
    if event.keysym.lower() not in utils.KEYBOARD_KEY_TO_LOCAL_NOTE:
        return
    localNote = utils.KEYBOARD_KEY_TO_LOCAL_NOTE[event.keysym.lower()]
    globalNote = localNote + LOWEST_NOTE
    noteReleased(globalNote)
    
