# Import Libraries
import os
import glob
import time
from datetime import datetime
#import onewiretemp as onewiretemp

#This class instantiates several versions

class aquarium:
    def __init__(self):
        self.aquariumID = 100
        self.aqtemp = onewiretemp.onewiretemp() #creates an temp object


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
