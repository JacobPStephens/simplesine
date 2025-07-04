import mido


# inport = mido.open_input()
# msg = inport.receive()
# print(msg)

# msg = mido.Message('note_on')

# print(msg)

# inport = None
# for port in mido.get_input_names():
portName = mido.get_input_names()[1]
print(f'{portName=}')
with mido.open_input(portName) as inport:
    print('listening...')
    for msg in inport:
        print('received', msg)



