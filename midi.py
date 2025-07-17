import mido
from simplesine import lock, notePlayed, noteReleased

# THIS FILE CANNOT IMPORT GUI


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
    
    with lock: 
        if msg.type == "note_on":
            notePlayed(msg.note)
            
        elif msg.type == "note_off":
            noteReleased(msg.note)
