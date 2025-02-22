# Jaikrishna
# Initial Date: June 26, 2013
# Last Updated: June 27, 2013

# This file is for interfacing Scratch with BrickPi
# The Python program acts as the Bridge between Scratch & BrickPi and must be running for the Scratch program to run.
# Requirements :
# Prior to running this progam, ScratchPy must be installed on the system. Refer BrickPi documentation on how to install ScratchPy.
# The BrickPi python library file (BrickPi.py) must be placed in the same path as this file.
# Remote Sensor values must be enabled in Scratch
# This python code must be restarted everytime you need to run a new program. 
# To run this in python, Open up Terminal and navigate to the path using 'cd' command
# Then enter:
#	 python BrickPiScratch.py
# To exit python, press Ctrl+C or force close the Terminal

# Broadcasts from Python:
# 'READY' tells that BrickPi serial setup succeeded. Use 'When I receive READY' to specify starting point of program. 
# 'UPDATED' tells that sensor values of Scratch has been updated from BrickPi

# Broadcast from Scratch:
# 'SETUP' command sets up the sensor properties
# 'START' command tells RPi to start continuous transmission to BPi
# 'UPDATE' command calls for an updation of Sensor Values of Scratch
# 'STOP' command stops the continuous up
# SETUP and START must be done only once after configuring the Sensors. UPDATE is Required atleast once. 

# Setting Sensor type:

# S1 ULTRASONIC 
# S2 TOUCH
# S3 RAW
# S4 COLOR
# S3 FLEX
# S5 TEMP
# Note: Only these sensors are supported as of now. The first 4 are lego products while the last 2 are from DexterIndustries

# Enabling and Running Motors:

# MA E - Enable motor A
# MB D - Disable motor B
# MA 100 - Set MotorA speed to 100
# MB -50 - Set MotorB speed to -100


import scratch,sys,threading,math
from BrickPi import *

try:
    s = scratch.Scratch()
    
except scratch.ScratchError:
    print "Scratch is either not opened or remote sensor connections aren't enabled"
    sys.exit(0)
    
if s.connected:
    print "Connected to Scratch successfully"
else:
    sys.exit(0)

sensor = [ None, False , False , False , False ]
spec = [ None, 0 , 0 , 0 , 0 ]
stype = { 'ULTRASONIC' : TYPE_SENSOR_ULTRASONIC_CONT ,
'TOUCH' : TYPE_SENSOR_TOUCH ,
'COLOR' : TYPE_SENSOR_COLOR_FULL ,
'RAW' : TYPE_SENSOR_RAW,
'TEMP' : TYPE_SENSOR_RAW,
'FLEX' : TYPE_SENSOR_RAW}    

BrickPiSetup()


def comp(val , case):
    if val == None or val== 0:
        return 0
    if case == 1:
        return val-600
    elif case == 2 :
        _a = [0.003357042,         0.003354017,        0.0033530481,       0.0033536166]
        _b = [0.00025214848,       0.00025617244,      0.00025420230,      0.000253772]
        _c = [0.0000033743283,     0.0000021400943,    0.0000011431163,    0.00000085433271]
        _d = [-0.000000064957311, -0.000000072405219, -0.000000069383563, -0.000000087912262]
        RtRt25 = (float)(val) / (1023 - val)
        lnRtRt25 = math.log(RtRt25)
        if (RtRt25 > 3.277) :
                i = 0
        elif (RtRt25 > 0.3599) :
                i = 1
        elif (RtRt25 > 0.06816) :
                i = 2
        else :
                i = 3
        temp =  1.0 / (_a[i] + (_b[i] * lnRtRt25) + (_c[i] * lnRtRt25 * lnRtRt25) + (_d[i] * lnRtRt25 * lnRtRt25 * lnRtRt25))
        temp-=273
        return round(temp,2)

running = False

class myThread (threading.Thread):      #This thread is used for continuous transmission to BPi while main thread takes care of Rx/Tx Broadcasts of Scratch
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        while running:
            BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
            time.sleep(.2)              # sleep for 200 ms

thread1 = myThread(1, "Thread-1", 1)        #Setup and start the thread
thread1.setDaemon(True)

s.broadcast('READY')

while True:
    try:
        m = s.receive()
        
        while m[0] == 'sensor-update' :
            m = s.receive()

        msg = m[1]
        if msg == 'SETUP' :
            BrickPiSetupSensors()
            print "Setting up sensors done"
        elif msg == 'START' :
            running = True 
            thread1.start()
            print "Service Started"
        elif msg == 'STOP' :
            running = False
        elif msg == 'UPDATE' :
            if sensor[1] :
                if spec[1] :
                    s.sensorupdate({'S1' : comp(BrickPi.Sensor[PORT_1],spec[1])})
                else:                
                    s.sensorupdate({'S1' : BrickPi.Sensor[PORT_1]})
            if sensor[2] :
                if spec[2] :
                    s.sensorupdate({'S2' : comp(BrickPi.Sensor[PORT_2],spec[2])})
                else :
                    s.sensorupdate({'S2' : BrickPi.Sensor[PORT_2]})
            if sensor[3] :
                if spec[3] :
                    s.sensorupdate({'S3' : comp(BrickPi.Sensor[PORT_3],spec[3])})
                else :
                    s.sensorupdate({'S3' : BrickPi.Sensor[PORT_3]})
            if sensor[4] :
                if spec[4] :
                    s.sensorupdate({'S4' : comp(BrickPi.Sensor[PORT_4],spec[4])})
                else:
                    s.sensorupdate({'S4' : BrickPi.Sensor[PORT_4]})
            s.broadcast('UPDATED')
        elif msg[:2] == 'S1' :
            if msg[2:].strip() == 'FLEX' :
                spec[1] = 1
            elif msg[2:].strip() == 'TEMP' :
                spec[1] = 2
            BrickPi.SensorType[PORT_1] = stype[msg[2:].strip()]
            sensor[1] = True
        elif msg[:2] == 'S2' :
            if msg[2:].strip() == 'FLEX' :
                spec[2] = 1
            elif msg[2:].strip() == 'TEMP' :
                spec[2] = 2
            BrickPi.SensorType[PORT_2] = stype[msg[2:].strip()]
            sensor[2] = True
        elif msg[:2] == 'S3' :
            if msg[2:].strip() == 'FLEX' :
                spec[3] = 1
            elif msg[2:].strip() == 'TEMP' :
                spec[3] = 2
            BrickPi.SensorType[PORT_3] = stype[msg[2:].strip()]
            sensor[3] = True
        elif msg[:2] == 'S4' :
            if msg[2:].strip() == 'FLEX' :
                spec[4] = 1
            elif msg[2:].strip() == 'TEMP' :
                spec[4] = 2
            BrickPi.SensorType[PORT_4] = stype[msg[2:].strip()]
            sensor[4] = True
        elif msg == 'MA E' or msg == 'MAE' :
            BrickPi.MotorEnable[PORT_A] = 1
        elif msg == 'MB E' or msg == 'MBE' :
            BrickPi.MotorEnable[PORT_B] = 1
        elif msg == 'MC E' or msg == 'MCE' :
            BrickPi.MotorEnable[PORT_C] = 1
        elif msg == 'MD E' or msg == 'MDE' :
            BrickPi.MotorEnable[PORT_D] = 1
        elif msg == 'MA D' or msg == 'MAD' :
            BrickPi.MotorEnable[PORT_A] = 0
        elif msg == 'MB D' or msg == 'MBD' :
            BrickPi.MotorEnable[PORT_B] = 0
        elif msg == 'MC D' or msg == 'MCD' :
            BrickPi.MotorEnable[PORT_C] = 0
        elif msg == 'MD D' or msg == 'MDD' :
            BrickPi.MotorEnable[PORT_D] = 0
        elif msg[:2] == 'MA' :
            BrickPi.MotorSpeed[PORT_A] = int(msg[2:])
        elif msg[:2] == 'MB' :
            BrickPi.MotorSpeed[PORT_B] = int(msg[2:])
        elif msg[:2] == 'MC' :
            BrickPi.MotorSpeed[PORT_C] = int(msg[2:])
        elif msg[:2] == 'MD' :
            BrickPi.MotorSpeed[PORT_D] = int(msg[2:])
    except KeyboardInterrupt:
        running= False
        print "Disconnected from Scratch"
        break
