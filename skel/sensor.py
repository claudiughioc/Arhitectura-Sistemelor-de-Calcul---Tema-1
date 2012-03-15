"""
	ASC TEMA 1
"""

from threading import *
import time
import random

SENSOR_TYPES = {"TEMP":0, "LIGHT":1, "PRESSURE":2, "HUMIDITY":3, "DISTANCE":4}
TEMP_RANGE = range(-40,55,1)
DELAY_RANGE =  [round(x/1000.0,3) for x in range (0, 200, 1)] # delay intre 0 si 0.2 secunde, round nu functioneaza

def setDelayRange(delayRange):
    DELAY_RANGE = delayRange

class Sensor:

    """
        Class representing a Sensor.
    """

    def __init__(self, seed = 0, sensorType = SENSOR_TYPES["TEMP"]):
        """ 
            Constructor.
            @param seed: the pseudo-random generator seed for simulating sensor values and response delays, default value 0
            @param sensorType: the type of sensor, as defined by SENSOR_TYPES variable, default value is temperature

        """
        self.sensorType = sensorType
        self.randGen = random.Random()
        self.randGen.seed(seed)
        self.delay = 0
        self.value = -1

    def getValue(self):
        """ @return the sensor's value """
 
        # randomly generate the response delay 
        self.delay = self.randGen.choice(DELAY_RANGE)
        time.sleep(self.delay)
        return self.value

    def getType(self):
        """ @return the sensor's type """

        return self.sensorType
    
    def nextPhase(self):
        """ For testing purposes the sensor must be aware of the current aggregation step. It provides the same value
            during the whole step """

        if self.sensorType == SENSOR_TYPES["TEMP"]:
            self.value = self.randGen.choice(TEMP_RANGE)
        else:
            self.value = self.randGen.randint(0, 100)
