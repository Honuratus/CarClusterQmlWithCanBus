import struct
import subprocess

JS_EVENT_SIZE = 8
JS_BUTTON = 0x01

START_BUTTON_NUMBER = 9  # <-- change this to your Start button number

def main():
    print("Waiting for Start button press on /dev/input/js0...")
    with open('/dev/input/js0', 'rb') as jsdev:
        while True:
            evbuf = jsdev.read(JS_EVENT_SIZE)
            if evbuf:
                time, value, type, number = struct.unpack('IhBB', evbuf)
                if type & JS_BUTTON:
                    if number == START_BUTTON_NUMBER and value == 1:  # pressed
                        print("Start button pressed! Launching your app...")
                        subprocess.Popen(['python3', '/path/to/your/app.py'])
                        break

if __name__ == "__main__":
    main()
