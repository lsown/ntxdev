# Import Libraries
import os
import glob
import time
from datetime import datetime

#Rpi related objects
from RPi import GPIO as GPIO
GPIO.setmode(GPIO.BCM)
import drv8830 #motor drive library
import i2cdisplay

#fake rpi objects - use these when rpi not available
"""
#note this is a local pointer, adjust reference locale as needed.
import sys
sys.path.insert(1, '/Users/lsown/Desktop/ntxdev/simPi') 

import sim_RPi
import sim_drv8830
import sim_i2cdisplay

"""

"""
Notes to remember:
level sensors - signal goes HIGH when water detected
motor fault pins - need to configure for pullup, these go low when fault detected
button - we may want to add 0.1 uF to c7. Hi when button depressed.
"""

class aquarium:
    def __init__(self):
        
        self.aquariumID = 100
        self.buttonTime = 0
        import onewiretemp as onewiretemp
        self.aqtemp = onewiretemp.onewiretemp() #creates an temp object

        self.pinsIn = {
            #5 : {'name' : 'lvlEN', 'pinType': 'levelSensor', 'state' : 0},
            6 : {'name' : 'wastelvl', 'pinType': 'levelSensor', 'state' : 0},
            19 : {'name' : 'cleanlvl', 'pinType': 'levelSensor', 'state' : 0},
            13 : {'name' : 'aqualvl', 'pinType': 'levelSensor', 'state' : 0},
            26 : {'name' : 'sparelvl', 'pinType': 'levelSensor', 'state' : 0},
            17 : {'name' : 'FAULTn1', 'pinType': 'motor', 'state' : 0},
            27 : {'name' : 'FAULTn2', 'pinType': 'motor', 'state' : 0},
            22 : {'name' : 'FAULTn3', 'pinType': 'motor', 'state' : 0},
            23 : {'name' : 'buttonSig', 'pinType': 'interface', 'state' : 0, 'priorState' : 0},
        }
        self.pinsOut = {
            #24 : {'name' : 'I2C RST', 'state' : 0},
            'LEDPwr' : {'name' : 'LEDPwr', 'state' : 0, 'pin' : 25},
            'stepDir' : {'name' : 'stepDir', 'state' : 0, 'pin' : 21},
            'stepEn' : {'name' : 'stepEn', 'state' : 1, 'pin' : 20}, 
            'stepStep' : {'name' : 'stepStep', 'state' : 0, 'pin' : 18}
        }
        self.motors = {
            'drv0' : {'name' : 'wastePump', 'i2cAddress' : 0x60, 'speed' : 0, 'direction' : 'cw', 'faultpin' : 17, 'state' : 'cw: 0'},
            'drv1' : {'name' : 'containerPump', 'i2cAddress' : 0x61, 'speed' : 0, 'direction' : 'cw', 'faultpin' : 27, 'state' : 'cw: 0'},
            #'drv2' : {'name' : 'sparePump', 'i2cAddress' : 0x62, 'speed' : 0, 'direction' : 'cw', 'faultpin': 22}
        }

        self.piSetup() #sets up the pi pin configurations
        self.drv8830Setup() #sets up the channels for i2c motor drivers

        self.display = i2cdisplay.display() #creates a display object
        self.display.drawStatus(
            text1='Welcome!', 
            text2=('temp: %s' %(str(self.get_temp())) 
                )
            )

    def piSetup(self): #Sets up GPIO pins, can also add to GPIO.in <pull_up_down=GPIO.PUD_UP>

        for pin in self.pinsOut:
            GPIO.setup(self.pinsOut[pin]['pin'], GPIO.OUT, initial = GPIO.LOW)
            print('0')

        for pin in self.pinsIn:
            GPIO.setup(pin, GPIO.IN)
            print(str(pin) + ' passed 1')
            self.pinsIn[pin]['state'] = GPIO.input(pin)
            print(str(pin) + ' passed 2')

            if self.pinsIn[pin]['pinType'] == 'levelSensor':
                GPIO.add_event_detect(pin, GPIO.BOTH, callback=self.levelSensor, bouncetime=100) 
                print(str(pin) + ' set as levelSensor callback')
            elif self.pinsIn[pin]['pinType'] == 'motor':
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.motorFault, bouncetime=100) 
                print(str(pin) + ' set as motor callback')
            elif self.pinsIn[pin]['pinType'] == 'interface':
                GPIO.add_event_detect(pin, GPIO.RISING, callback=self.buttonPress, bouncetime=100) 
                print(str(pin) + ' set as button callback')
            print(str(pin) + ' passed 3')

    def drv8830Setup(self):
        self.drv0 = drv8830.DRV8830(i2c_addr=0x60)
        self.drv1 = drv8830.DRV8830(i2c_addr=0x61)
        #self.drv2 = drv8830.DRV8830(i2c_addr=0x62) #note, change HW to 0x63 to work with library

    def buttonPress(self, channel):
        print('button press detected: ' + 'prior state was ' + str(self.pinsIn[channel]['priorState']))
        if ((time.time() - self.buttonTime) > 1):    
            self.pinsIn[channel]['state'] = GPIO.input(channel) #set state to 1
            if self.pinsIn[channel]['priorState'] == 0:
                GPIO.output(self.pinsOut['LEDPwr']['pin'], 1)
                self.pinsIn[channel]['priorState'] = 1
                self.motorControl(name='drv0', speed = 1, direction = 'forward')
                self.display.drawStatus(text1='pumping', text2=('temp: ' + str(self.get_temp())))
            else:
                GPIO.output(self.pinsOut['LEDPwr']['pin'], 0)
                self.pinsIn[channel]['priorState'] = 0
                self.motorControl(name='drv0', speed = 0, direction = 'brake')
                self.display.drawStatus(text1='idle', text2=('temp: ' + str(self.get_temp())))
            print('LED state changed to ' + str(self.pinsIn[channel]['priorState']))
            self.buttonTime = time.time() #sets a time for last button press

    def levelSensor(self, channel):
        self.pinsIn[channel]['state'] = GPIO.input(channel) #set state to 1
        if self.pinsIn[channel]['state'] == 1:
            print("pin state set to" + str(self.pinsIn[channel]['state'])) # debug
            if self.pinsIn[channel]['name'] == 'wastelvl':
                print('wastelvl went high')
            elif self.pinsIn[channel]['name'] == 'cleanlvl':
                print('cleanlvl went high')
            elif self.pinsIn[channel]['name'] == 'aqualvl':
                print('aqualvl went high, turning off motors')
                self.motorControl(name='drv0', speed=0, direction = 'brake')
                self.display.drawStatus(text1='Aqua Hi', text2=('temp: ' + str(self.get_temp())))
            elif self.pinsIn[channel]['name'] == 'sparelvl':
                print('sparelvl went high')
        else:
            self.pinsIn[channel]['state'] = 0
            print("pin state set to" + str(self.pinsIn[channel]['state'])) # debug
 

    def resetState(self, channel):
        self.pinsIn[channel]['state'] = 0
        print("pin state set to" + self.pinsIn[channel]['state']) # debug


    def motorFault(self, channel):
        #GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback, bouncetime=200)
        for i in self.motors:
            if self.motors[i]['faultpin'] == channel:
                print(i + "has tripped a fault")

    def motorControl(self, name='drv0', i2cAddress=0x60, speed=1, direction='forward'):
        if speed > 1:
            speed = 1
        voltage = (2 * float(speed)) + 3 #looks like min. speed of our pump is 3V

        if name == 'drv0':
            self.drv0.set_direction(direction)
            self.drv0.set_voltage(voltage)
            print("Setting direction " + name + " " + direction + " " + str(voltage))

        if name == 'drv1':
            self.drv1.set_direction(direction)
            self.drv1.set_voltage(voltage)
            print("Setting direction " + name + direction + " " + str(voltage))

        self.motors[name]['speed'] = speed
        self.motors[name]['direction'] = direction
        self.motors[name]['state'] = (direction + " direction @ speed " + str(speed))

    def stateMonitor(self):
        #detects if level sensors have gone high
        return('hi')

    def get_status(self):
        return {
            'temp': self.get_temp(),
            'motor1' : self.motors['drv0']['state'],
            'motor2' : self.motors['drv0']['state'],
            'AqFlag' : self.pinsIn[13]['state'],
            'CleanFlag' : self.pinsIn[19]['state'],
            'WasteFlag' : self.pinsIn[6]['state'],
            'SpareFlag' : self.pinsIn[26]['state'],
            'time' : datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        } #0 is celcius, 1 is farenheit

    def get_temp(self):
        return self.aqtemp.read_temp()[0] #0 is celcius, 1 is farenheit
