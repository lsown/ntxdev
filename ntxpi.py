# Import Libraries
import os
import glob
import time
from datetime import datetime
import threading
import random

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

        #simulated version 
        self.aqdict_sim = {
            'temp': random.randrange(0, 50),
            'drv0' : True if random.randrange(0,2) == 0 else False,
            'drv1' : True if random.randrange(0,2) == 0 else False,
            'drv0Spd' : 0,
            'drv1Spd' : 0,
            'aquaFlag' : random.randrange(0,2),
            'cleanFlag' : random.randrange(0,2),
            'wasteFlag' : random.randrange(0,2),
            'spareFlag' : random.randrange(0,2),
            'exchangeState' : False,
            'tempmax' : 40,
            'tempmin' : 10
            }

        import onewiretemp as onewiretemp
        self.aqtemp = onewiretemp.onewiretemp() #creates an temp object

        self.pinsIn = {
            #5 : {'name' : 'lvlEN', 'pinType': 'levelSensor', 'state' : 0},
            'buttonSig' : {'name' : 'buttonSig', 'pinType': 'interface', 'state' : 0, 'priorState' : 0, 'pin' : 23},
            'wasteFlag' : {'name' : 'wasteFlag', 'pinType': 'levelSensor', 'state' : 0, 'pin' : 6},
            'cleanFlag' : {'name' : 'cleanFlag', 'pinType': 'levelSensor', 'state' : 0, 'pin' : 19},
            'aquaFlag' : {'name' : 'aquaFlag', 'pinType': 'levelSensor', 'state' : 0, 'pin' : 13},
            'spareflag' : {'name' : 'SpareFlag', 'pinType': 'levelSensor', 'state' : 0, 'pin' : 26},
            'FAULTn1' : {'name' : 'FAULTn1', 'pinType': 'motor', 'state' : 0, 'pin' : 17},
            'FAULTn2' : {'name' : 'FAULTn2', 'pinType': 'motor', 'state' : 0, 'pin' : 27},
            'FAULTn3' : {'name' : 'FAULTn3', 'pinType': 'motor', 'state' : 0, 'pin' : 22},
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

        for i in self.pinsOut:
            GPIO.setup(self.pinsOut[i]['pin'], GPIO.OUT, initial = self.pinsOut[i]['state']) #set GPIO as OUT, configure initial value
            print('%s configured as OUTPUT %s' %(str(self.pinsOut[i]['pin']), self.pinsOut[i]['state']))

        for i in self.pinsIn:
            GPIO.setup(self.pinsIn[i]['pin'], GPIO.IN) #set GPIO as INPUT
            print('Pin %s configured as INPUT' %(str(self.pinsIn[i]['pin'])))

            self.pinsIn[i]['state'] = GPIO.input(self.pinsIn[i]['pin'])
            print('%s initial state is %s' %(self.pinsIn[i]['name'], str(self.pinsIn[i]['state'])))

            #configure event detections for pinType levelSensor & interface
            if self.pinsIn[i]['pinType'] == 'levelSensor':
                GPIO.add_event_detect(i, GPIO.BOTH, callback=self.levelSensor, bouncetime=100) 
                print('%s set as levelSensor callback' %(str(self.pinsIn[i]['name'])))
            elif self.pinsIn[i]['pinType'] == 'interface':
                GPIO.add_event_detect(i, GPIO.RISING, callback=self.buttonPress, bouncetime=100) 
                print('%s set as button callback' %(str(self.pinsIn[i]['name'])))

            #elif self.pinsIn[i]['pinType'] == 'motor':
                #GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.motorFault, bouncetime=100) 
                #print(str(self.pinsIn[i]['pin']) + ' set as motor callback')

    def drv8830Setup(self):
        self.drv0 = drv8830.DRV8830(i2c_addr=0x60)
        self.drv1 = drv8830.DRV8830(i2c_addr=0x61)
        #self.drv2 = drv8830.DRV8830(i2c_addr=0x62) #note, change HW to 0x63 to work with library

    def get_status(self):
        return {
            'temp': self.get_temp(), #0 is celcius, 1 is farenheit
            'motor1' : self.motors['drv0']['state'],
            'motor2' : self.motors['drv0']['state'],
            'AqFlag' : self.pinsIn['AqFlag']['state'],
            'CleanFlag' : self.pinsIn['CleanFlag']['state'],
            'WasteFlag' : self.pinsIn['WasteFlag']['state'],
            'SpareFlag' : self.pinsIn['SpareFlag']['state'],
            'time' : datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        } #0 is celcius, 1 is farenheit

    def get_temp(self):
        return self.aqtemp.read_temp()[0]

    def buttonPress(self, channel):
        print('button press detected: prior state was %s' %(str(self.pinsIn[channel]['priorState'])))
        if ((time.time() - self.buttonTime) > 1):    
            self.pinsIn[channel]['state'] = GPIO.input(channel) #set state to 1
            if self.pinsIn[channel]['priorState'] == 0:
                GPIO.output(self.pinsOut['LEDPwr']['pin'], 1)
                self.pinsIn[channel]['priorState'] = 1
                self.motorControl(name='drv0', speed = 1, direction = 'forward')
                self.display.drawStatus(text1='pumping', text2=('temp: %s' %(str(self.get_temp()))))
            else:
                GPIO.output(self.pinsOut['LEDPwr']['pin'], 0)
                self.pinsIn[channel]['priorState'] = 0

                self.motorControl(name='drv0', speed = 0, direction = 'brake')
                self.display.drawStatus(text1='idle', text2=('temp: %s' %(str(self.get_temp()))))
            print('LED state changed to ' + str(self.pinsIn[channel]['priorState']))
            self.buttonTime = time.time() #sets a time for last button press

    def levelSensor(self, channel):
        if GPIO.input(channel['pin']) == 1:
            self.pinsIn[channel]['state'] = GPIO.input(channel['pin']) #set state to the input
            print("%s state set to %s" %(self.pinsIn[channel]['name'], str(self.pinsIn[channel]['state']))) # debug
            if self.pinsIn[channel]['name'] == 'aquaFlag':
                print('aqualvl went high, turning off motors')
                self.motorControl(name='drv0', speed=0, direction = 'brake')
                self.display.drawStatus(text1='Aqualevel Hi', text2=('temp: ' + str(self.get_temp())))
        if GPIO.input(channel['pin']) == 0:
            self.pinsIn[channel]['state'] = 0
            print("pin state set to %s" %(self.pinsIn[channel]['name'], str(self.pinsIn[channel]['state']))) # debug
 

    def resetState(self, channel):
        self.pinsIn[channel]['state'] = 0
        print("pin state set to %s" %(self.pinsIn[channel]['state'])) # debug


    def motorFault(self, channel):
        #GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback, bouncetime=200)
        for i in self.motors:
            if self.motors[i]['faultpin'] == channel:
                print("%s has tripped a fault" %(str(i)))

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

    def drv8825(self, frequency, direction, steps, stepEnPin = 20, stepDirPin = 21, stepStepPin = 18):
        stepTime = 1/frequency/2 #duration for high, duration for low
        totalTime = 1/frequency * steps #calculates total estimated time for routine to finish
        if direction == 1:
            GPIO.output(stepDirPin, 1)
        else:
            GPIO.output(stepDirPin, 0)
        GPIO.output(stepEnPin, 0) #enable drv8825 chip
        print("Stepper enabled, estimated time %s" %(str(totalTime)))
        count = 0
        while count <= steps:
            GPIO.output(stepStepPin, 1)
            time.sleep(stepTime)
            GPIO.output(stepStepPin,0)
            time.sleep(stepTime)
            count += 1
        print("Steppers finished %s steps at frequency %s" % (steps, frequency))
        GPIO.output(stepEnPin,1) #disable stepper power
        print("Stepper disabled")
'''
class myThread (threading.Thread):
   def __init__(self, threadID, name, counter, functionPass):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      print("Starting thread: " + self.name)
      self.functionPass
      print("Exiting thread: " + self.name)
'''