#Rpi related objects
from RPi import GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
import time

for pin in [38,40,12]:
    GPIO.setup(pin, GPIO.OUT)
    if pin == 38:
        GPIO.output(pin, 1)
    else:
        GPIO.output(pin, 0)

def motor(frequency, direction, steps):
    count = 0
    stepTime = 1/frequency/2 #
    totalTime = 1/frequency * steps
    if direction == 1:
        GPIO.output(40, 1)
    else:
        GPIO.output(40, 0)
    GPIO.output(38, 0)
    print("Stepper enabled, estimated time %s" %(str(totalTime)))
    while count <= steps:
        GPIO.output(12, 1)
        time.sleep(stepTime)
        GPIO.output(12,0)
        time.sleep(stepTime)
        count += 1
    print("Steppers finished %s steps at frequency %s" % (steps, frequency))
    GPIO.output(38,1)
    print("Stepper disabled")
