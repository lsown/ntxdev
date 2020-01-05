# Import Libraries
import os
import glob
import time
import onewiretemp as onewiretemp

#This class instantiates several versions

class aquarium:
    def __init__(self):
        self.aqariumID = 100
        self.aqtemp = onewiretemp.onewiretemp() #creates an temp object

    def get_status(self):
        return self.aqtemp.read_temp()[0] #0 is celcius, 1 is farenheit