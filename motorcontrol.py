import RPi.GPIO as GPIO
from time import sleep
from RpiMotorLib import RpiMotorLib


# https://iotdesignpro.com/projects/raspberry-pi-stepper-motor-control-through-a-webpage-using-flask


class Nema17Motor:
    def __init__(
        self, GPIO_pins, direction, step, spulenumfang, steps_per_revolution
    ):  # format: (Step-MS1, Direction-MS2, Microstep-MS3), DirectionPin, StepPin, Abrolllänge der Spule, Steps per Umdrehung
        self.motordef = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")
        self.revolution = spulenumfang
        self.steps_per_revolution = steps_per_revolution

    def moveMotor(self, length, speed):  # speed: mm/s, length: mm
        if length == 0:
            return
        if length < 0:
            clockwise = True
            length = length * -1
        else:
            clockwise = False
        # ----- Calculate number of steps necessary -----
        steps = self.revolution // length
        steps = steps * self.steps_per_revolution

        # ----- Calculate length of single step -----
        # single_step = self.revolution // self.steps_per_revolution

        # ----- Calculate delay between steps -----
        step_delay = speed // steps

        self.motordef.motor_go(
            clockwise, "Full", steps, step_delay * 0.001, False, 0.05
        )


class ServoMotor:
    def __init__(self, controlpin):
        self.control_pin = controlpin

        GPIO.setmode(GPIO.BOARD)
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
