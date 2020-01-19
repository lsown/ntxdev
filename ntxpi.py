# Import Libraries
import os
import glob
import time
from datetime import datetime

#Rpi related objects

from RPi import GPIO as GPIO
GPIO.setmode(GPIO.BCM)
#This class instantiates several versions

class aquarium:
    def __init__(self):
        
        self.aquariumID = 100
        import onewiretemp as onewiretemp
        self.aqtemp = onewiretemp.onewiretemp() #creates an temp object
        '''
        self.pinsIn = {
            5 : {'name' : 'lvlEN', 'pinType': 'levelSensor', 'state' : 1},
            6 : {'name' : 'wastelvl', 'pinType': 'levelSensor', 'state' : 0}
            }
        '''
        self.pinsIn = {
            5 : {'name' : 'lvlEN', 'pinType': 'levelSensor', 'state' : 0},
            6 : {'name' : 'wastelvl', 'pinType': 'levelSensor', 'state' : 0},
            13 : {'name' : 'cleanlvl', 'pinType': 'levelSensor', 'state' : 0},
            19 : {'name' : 'aqualvl', 'pinType': 'levelSensor', 'state' : 0},
            26 : {'name' : 'sparelvl', 'pinType': 'levelSensor', 'state' : 0},
            17 : {'name' : 'FAULTn1', 'pinType': 'motor', 'state' : 0},
            27 : {'name' : 'FAULTn2', 'pinType': 'motor', 'state' : 0},
            22 : {'name' : 'FAULTn3', 'pinType': 'motor', 'state' : 0},
            23 : {'name' : 'buttonSig', 'pinType': 'interface', 'state' : 0},
        }
        self.pinsOut = {
            #24 : {'name' : 'I2C RST', 'state' : 0},
            18 : {'name' : 'LEDPwr', 'state' : 0} 
        }
        self.motors = {
            'drv1' : {'name' : 'aqPump', 'i2cAddress' : 0x60, 'voltage' : 0, 'direction' : 'cw'},
            'drv2' : {'name' : 'wastePump', 'i2cAddress' : 0x61, 'voltage' : 0, 'direction' : 'cw'},
            'drv3' : {'name' : 'sparePump', 'i2cAddress' : 0x62, 'voltage' : 0, 'direction' : 'cw'}
        }
        self.piSetup()
        

    def piSetup(self): #Sets up GPIO pins, can also add to GPIO.in <pull_up_down=GPIO.PUD_UP>

        for pin in self.pinsOut:
            GPIO.setup(pin, GPIO.OUT, initial = GPIO.LOW)
            print('0')
        for pin in self.pinsIn:
            GPIO.setup(pin, GPIO.IN)
            print(str(pin) + ' passed 1')
            self.pinsIn[pin]['state'] = GPIO.input(pin)
            print(str(pin) + 'passed 2')
            if self.pinsIn[pin]['pinType'] == 'levelSensor':
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.levelSensor, bouncetime=10) 
                print(str(pin) + 'set as levelSensor callback')
            elif self.pinsIn[pin]['pinType'] == 'motor':
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.motorFault, bouncetime=10) 
                print(str(pin) + 'set as motor callback')
            elif self.pinsIn[pin]['pinType'] == 'interface':
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.buttonPress, bouncetime=10) 
                print(str(pin) + 'set as button callback')
            print(str(pin) + 'passed 3')

    def buttonPress(self, channel):
        #GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback, bouncetime=200)
        print('button')
        print(channel)

    def levelSensor(self, channel):
        #GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback, bouncetime=200)
        

    def motorFault(self, channel):
        #GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback, bouncetime=200)
        print('hi')

    def stateMonitor(self):
        #detects if level sensors have gone high
        return('hi')

    def get_status(self):
        return {
            'temp': self.get_temp(),
            'motor1' : 'ON',
            'motor2' : 'OFF',
            'AqFlag' : 'LOW',
            'ExFlag' : 'LOW',
            'time' : datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        } #0 is celcius, 1 is farenheit

    def get_temp(self):
        return self.aqtemp.read_temp()[0] #0 is celcius, 1 is farenheit

    def readPin(self):
        try:
            GPIO.setup(int(pin), GPIO.IN)
            if GPIO.input(int(pin)) == True:
                response = "Pin number " + pin + " is high!"
            else:
                response = "Pin number " + pin + " is low!"
        except:
          response = "There was an error reading pin " + pin + "."