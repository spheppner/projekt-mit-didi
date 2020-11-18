import RPi.GPIO as GPIO
from time import sleep

from RpiMotorLib import RpiMotorLib
import threading
import queue


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


if __name__ == "__main__":
    hmotor = Nema17MotorHandler(Nema17Motor((14, 15, 18), 20, 21, 100, 200, 0.05))

    hmotor.start()

    hmotor.queue.put({"command": "move", "attributes": (50, 10)})
    hmotor.queue.put({"command": "move", "attributes": (50, 50)})
    hmotor.queue.put({"command": "move", "attributes": (100, 50)})
    hmotor.queue.put({"command": "move", "attributes": (-100, 50)})
    hmotor.queue.put({"command": "move", "attributes": (-50, 50)})
    hmotor.queue.put({"command": "move", "attributes": (50, 10)})

    while not hmotor.queue.empty():
        pass

    hmotor.kill()
    hmotor.join()
