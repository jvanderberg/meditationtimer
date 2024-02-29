import board
import busio
import digitalio
import time
import adafruit_mma8451
import math
from adafruit_soundboard import Soundboard


def remove_outliers(arr):
    outliers = []
    for i in range(1, len(arr) - 2):
        last = arr[i - 1] - arr[i]
        next = arr[i + 1] - arr[i]
        if ((last < 10 and next < 10) or (last > -10 and next > -10)):
            outliers.append(arr[i])
    return outliers


intervals = [1, 2, 3, 4, 5, 6, 8, 10]
lengths = [60, 55, 45, 30, 20, 15, 10, 5]
interval_offset = 6

length_offset = 4

sounds = ["BUZZ    OGG", "BELL    OGG", "GONG    OGG", "BING    OGG",
          "BOWL    OGG", "TING    OGG", "BEEP    OGG", "CLANG   OGG"]
sound_offset = 4


def reset_soundboard(sb):
    sb._send_simple(b"q")


def playsound(sb, sound):
    sb._send_simple(bytes("P"+sound, "utf-8"))


class Accelerometer:
    def __init__(self, sda, scl):
        self.sda = sda
        self.scl = scl
        self.history = []
        self.angle = 0
        self.last_angle = 0
        self.last_angle_set = 0

        self.change_time = 0  # Variable to store the time of change

    def add_change(self, change):
        # Record the current time of change
        current_time = time.time()

        # If this is the first change, record the change and its time
        if self.firstChange is None:
            self.firstChange = change
            self.change_time = current_time

        # Append the change to the history
        self.history.append((change, current_time))

    def is_changed(self):
        change = abs(self.angle - self.last_angle)

        if (change > 3):
            # There's been some change, start a timer
            self.change_time = time.monotonic()

        # If there's been no change in the last 2 seconds, check to see if the
        # the current angle is different from the last angle set, if so,
        # set a new angle, and return true
        if (time.monotonic() - self.change_time > 2 and self.change_time != 0):
            self.change_time = 0
            if (abs(self.angle - self.last_angle_set) > 5):
                self.last_angle_set = self.angle
                return True

        return False

    def read_angle(self):
        try:
            accel = busio.I2C(self.scl, self.sda)
            sensor = adafruit_mma8451.MMA8451(accel)
            x, y, z = sensor.acceleration
            if (x == 0):
                x = 0.001
            angle = math.atan(z / x) * 360 / math.pi / 2
            if x < 0:
                angle = 180 - math.atan(z / -x) * 360 / math.pi / 2
            else:
                if z < 0:
                    angle = 360 + math.atan(z / x) * 360 / math.pi / 2

            if (y == 0):
                y = 0.001

            accel.deinit()
            self.history.append(angle)
            if (len(self.history) > 10):
                self.history.pop(0)

            if (len(self.history) > 3):
                cleaned = remove_outliers(self.history)

            else:
                cleaned = self.history

            angle = cleaned[0]
            for i in range(1, len(cleaned)-1):
                angle = 0.9 * angle + 0.1 * cleaned[i]

            self.angle = angle
            is_changed = self.is_changed()
            self.last_angle = angle
            position = -1
            if self.last_angle_set > 80 and self.last_angle_set < 110:
                position = 1
            if self.last_angle_set > 35 and self.last_angle_set < 55:
                position = 8
            if self.last_angle_set < 10 or self.last_angle_set > 350:
                position = 7
            if self.last_angle_set > 125 and self.last_angle_set < 145:
                position = 2
            if self.last_angle_set > 170 and self.last_angle_set < 200:
                position = 3
            if self.last_angle_set > 215 and self.last_angle_set < 235:
                position = 4
            if self.last_angle_set > 260 and self.last_angle_set < 280:
                position = 5
            if self.last_angle_set > 305 and self.last_angle_set < 325:
                position = 6

            if (is_changed):
                return position, True

            return position, False
        except Exception as e:
            print(e, self.sda, self.scl)
            try:
                accel.deinit()
            except:
                pass
            return 0, False


led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
sound = Soundboard("GP0", "GP1", "GP2", debug=True, vol=None)
reset_soundboard(sound)

index = 0
last_position = 1
angle1 = 90
history1 = []
angle2 = 90
history2 = []
angle3 = 90
history3 = []
change_time = 0
firstchange = 0
lastangle2 = 0
last_angle_set2 = 0
interval = -1
duration = -1
selectedSound = ""
programStartTime = -1
intervalStartTime = -1
accel1 = Accelerometer(scl=board.GP21, sda=board.GP20)
accel2 = Accelerometer(scl=board.GP17, sda=board.GP16)
accel3 = Accelerometer(scl=board.GP19, sda=board.GP18)

lastchange = time.monotonic()
change = False
while True:
    led.value = True
    time.sleep(0.01)
    led.value = False

    angle1, angle1_changed = accel2.read_angle()
    angle2, angle2_changed = accel1.read_angle()
    angle3, angle3_changed = accel3.read_angle()
    if (angle3_changed):
        interval = intervals[(angle3+interval_offset) % 8]
        lastchange = time.monotonic()
        change = True
        print('Interval ', interval)

    if (angle1_changed):
        duration = lengths[((angle1)+length_offset) % 8]
        lastchange = time.monotonic()
        change = True
        print('Duration', duration)

    if (angle2_changed):
        selectedSound = sounds[((angle2)+sound_offset) % 8]
        lastchange = time.monotonic()
        change = True
        print('Sound ', selectedSound)

    # Give a second for all of the readings to settle down and to set their new values
    if (change and time.monotonic() - lastchange > 1):

        # We have a change, restart the program and play the first sound, but make sure it's been more than a second since
        # the last restart
        print('Restarting...')
        programStartTime = time.monotonic()
        intervalStartTime = time.monotonic()
        success = False
        reset_soundboard(sound)
        playsound(sound, selectedSound)
        change = False

    if (programStartTime > 0 and time.monotonic() - programStartTime > duration * 60):
        # We are done
        print('Done')

        programStartTime = -1
        intervalStartTime = -1
        reset_soundboard(sound)
        playsound(sound, selectedSound)
        time.sleep(5)
        reset_soundboard(sound)
        playsound(sound, selectedSound)
        time.sleep(5)
        reset_soundboard(sound)
        playsound(sound, selectedSound)

    if (interval > 0 and programStartTime > 0 and time.monotonic() - intervalStartTime > (duration / interval) * 60):
        # We play a sound
        print('Play sound', time.monotonic() - intervalStartTime)
        print('Play sound', duration, interval)
        print('Play sound', (duration / interval) * 60)
        reset_soundboard(sound)
        playsound(sound, selectedSound)

        intervalStartTime = time.monotonic()
