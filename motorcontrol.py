import RPi.GPIO as GPIO
from time import sleep
from RpiMotorLib import RpiMotorLib
import threading
import queue
import math


__version__ = "1.0.0"
__author__ = "Simon HEPPNER; Dietmar TRUMMER"


# https://iotdesignpro.com/projects/raspberry-pi-stepper-motor-control-through-a-webpage-using-flask


class Nema17Motor:
    def __init__(
        self,
        GPIO_pins,
        direction_pin,
        step_pin,
        spulenumfang,
        steps_per_revolution,
        initial_delay,
    ):  # format: (MS1-BCM, MS2-BCM, MS3-BCM), DirectionPin-BCM, StepPin-BCM, Abrolllänge der Spule, Steps per Umdrehung, 0.05 Standardwert
        self.motordef = RpiMotorLib.A4988Nema(
            direction_pin, step_pin, GPIO_pins, "A4988"
        )
        self.revolution = spulenumfang
        self.steps_per_revolution = steps_per_revolution
        self.initial_delay = initial_delay
        self.position = 0

    def moveMotor(self, length, speed):  # speed: mm/s, length: mm
        if length == 0 or speed == 0:
            return
        if length < 0:
            clockwise = True
            length *= -1
        else:
            clockwise = False
        # ----- Calculate number of steps -----
        steps = length / self.revolution
        steps *= self.steps_per_revolution

        # ----- Calculate delay between steps -----
        duration = length / speed
        step_delay = duration / steps

        self.motordef.motor_go(
            clockwise, "Full", int(steps), step_delay, False, self.initial_delay
        )


class Nema17MotorHandler(threading.Thread):
    def __init__(self, motor):
        super().__init__()
        self.motor = motor
        self.running = True
        self.queue = queue.Queue(maxsize=100)

    def run(self):
        while self.running:
            c = self.queue.get()
            cname = c["command"]
            cattributes = c["attributes"]
            if cname == "move":
                self.motor.moveMotor(cattributes[0], cattributes[1])
                print(c)
        print("run finished")

    def kill(self):
        print("killed")
        self.running = False


class ServoMotor:
    def __init__(self, controlpin):  # format: controlpin-BCM
        self.control_pin = controlpin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.control_pin, GPIO.OUT)

        self.pwm = GPIO.PWM(self.control_pin, 50)
        self.pwm.start(0)

    def moveMotor(self, angle):
        duty = angle / 18 + 2
        GPIO.output(self.control_pin, True)
        self.pwm.ChangeDutyCycle(duty)
        sleep(1)
        GPIO.output(self.control_pin, False)
        self.pwm.ChangeDutyCycle(0)

    def kill(self):
        self.pwm.stop()
        GPIO.cleanup()


class Plotter(threading.Thread):
    def __init__(self):
        super().__init__()
        self.xmotor = Nema17MotorHandler(
            Nema17Motor((14, 15, 18), 20, 21, 100, 200, 0.05)
        )
        self.ymotor = Nema17MotorHandler(
            Nema17Motor((13, 6, 5), 26, 19, 100, 200, 0.05)
        )
        self.x = 0
        self.y = 0
        self.pendrawing = True
        self.queue = queue.Queue(maxsize=100)
        self.running = True

    def run(self):
        self.xmotor.start()
        self.ymotor.start()
        while self.running:
            c = self.queue.get()
            ccommand = c["command"]
            cattributes = c["attributes"]
            if ccommand == "draw-xy":
                self.handlePen(True)
                self.handleMotors(cattributes[0], cattributes[1], 40)
            elif ccommand == "move-xy":
                self.handlePen(False)
                self.handleMotors(cattributes[0], cattributes[1], 100)

    def handleMotors(self, x, y, speed):
        dx = x - self.x
        dy = y - self.y
        if dx == 0:
            vx = 0
            vy = speed
            if dy < 0:
                a = math.radians(-90)
            else:
                a = math.radians(90)
        else:
            a = math.atan(dy / dx)
            vx = math.cos(a) * speed
            vy = math.sin(a) * speed
        if vx != 0:
            self.xmotor.queue.put({"command": "move", "attributes": (dx, vx)})
        if vy != 0:
            self.ymotor.queue.put({"command": "move", "attributes": (dy, vy)})
        self.x += dx
        self.y += dy
        print(f"Penlength: {math.sqrt((dy**2+dx**2))} | Alpha: {math.degrees(a)}")
        print(f"X: {self.x} | Y: {self.y}")

    def handlePen(self, state):
        if self.pendrawing == state:
            return
        if state:
            self.pendrawing = True
            print("Pen down")
        else:
            self.pendrawing = False
            print("Pen up")

    def kill(self):
        self.running = False
        self.xmotor.kill()
        self.ymotor.kill()
        self.xmotor.join()
        self.ymotor.join()

    def calibrate(self):
        # TODO: implement calibration process
        self.x = 0
        self.y = 0


if __name__ == "__main__":
    plotter = Plotter()
    plotter.start()

    plotter.queue.put({"command": "move-xy", "attributes": (100, 100)})
    plotter.queue.put({"command": "draw-xy", "attributes": (90, 90)})
    plotter.queue.put({"command": "draw-xy", "attributes": (140, 90)})
    plotter.queue.put({"command": "draw-xy", "attributes": (140, 120)})
    plotter.queue.put({"command": "move-xy", "attributes": (0, 90)})
    plotter.queue.put({"command": "move-xy", "attributes": (0, 0)})

    while not plotter.queue.empty():
        pass

    plotter.kill()
    plotter.join()
