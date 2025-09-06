
import time


def check_device_output():
    import rtmidi
    midi_in = rtmidi.MidiIn()

    midi_in.open_port(0)

    while True:
        msg_and_dt = midi_in.get_message()

        if msg_and_dt:
            #unpack the msg and the time tuple
            (msg, dt) = msg_and_dt

            #convert the command integer to a hex so it's more readable
            command = hex(msg[0])
            print(f"{command} {msg[1:]}\t|  dt = {dt:.2f}")

        else:
            #add a short sleep so while loop doesn't wreck cpu
            time.sleep(0.001)

