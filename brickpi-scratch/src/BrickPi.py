# Jaikrishna
# Initial Date: June 24, 2013
# Last Updated: June 24, 2013
# http://www.dexterindustries.com/
#
# Ported from Matthew Richardson's BrickPi library for C 
# This library can be used in RaspberryPi to communicate with BrickPi
# Major Changes from C code:
# - The timeout parameter for BrickPiRx is in seconds expressed as a floating value
# - Instead of Call by Reference in BrickPiRx, multiple values are returned and then copied to the main Array appropriately
# - BrickPiStruct Variables are assigned to None and then modified to avoid appending which may lead to errors


import time
import serial
ser = serial.Serial()
ser.port='/dev/ttyAMA0'
ser.baudrate = 500000
# ser.writeTimeout = 0.0005		
# ser.timeout = 0.0001

DEBUG = 1	# Remove to hide errors 

PORT_A = 0
PORT_B = 1
PORT_C = 2
PORT_D = 3

PORT_1 = 0
PORT_2 = 1
PORT_3 = 2
PORT_4 = 3

MASK_D0_M = 0x01
MASK_D1_M = 0x02
MASK_9V   = 0x04
MASK_D0_S = 0x08
MASK_D1_S = 0x10

BYTE_MSG_TYPE        = 0 # MSG_TYPE is the first byte.
MSG_TYPE_CHANGE_ADDR = 1 # Change the UART address.
MSG_TYPE_SENSOR_TYPE = 2 # Change/set the sensor type.
MSG_TYPE_VALUES      = 3 # Set the motor speed and direction, and return the sesnors and encoders.
MSG_TYPE_E_STOP      = 4 # Float motors immidately

# New UART address (MSG_TYPE_CHANGE_ADDR)
BYTE_NEW_ADDRESS   = 1

# Sensor setup (MSG_TYPE_SENSOR_TYPE)
BYTE_SENSOR_1_TYPE = 1
BYTE_SENSOR_2_TYPE = 2

TYPE_MOTOR_PWM               = 0
TYPE_MOTOR_SPEED             = 1
TYPE_MOTOR_POSITION          = 2

TYPE_SENSOR_RAW              = 0 # - 31
TYPE_SENSOR_LIGHT_OFF        = 0
TYPE_SENSOR_LIGHT_ON         = (MASK_D0_M | MASK_D0_S)
TYPE_SENSOR_TOUCH            = 32
TYPE_SENSOR_ULTRASONIC_CONT  = 33
TYPE_SENSOR_ULTRASONIC_SS    = 34
TYPE_SENSOR_RCX_LIGHT        = 35 # tested minimally
TYPE_SENSOR_COLOR_FULL       = 36
TYPE_SENSOR_COLOR_RED        = 37
TYPE_SENSOR_COLOR_GREEN      = 38
TYPE_SENSOR_COLOR_BLUE       = 39
TYPE_SENSOR_COLOR_NONE       = 40
TYPE_SENSOR_I2C              = 41
TYPE_SENSOR_I2C_9V           = 42

BIT_I2C_MID  = 0x01  # Do one of those funny clock pulses between writing and reading. defined for each device.
BIT_I2C_SAME = 0x02  # The transmit data, and the number of bytes to read and write isn't going to change. defined for each device.

INDEX_RED   = 0
INDEX_GREEN = 1
INDEX_BLUE  = 2
INDEX_BLANK = 3

Array = [0] * 256
BytesReceived = None
Bit_Offset    = 0
Retried = 0

class BrickPiStruct:
    Address = [ 1, 2 ]

    MotorSpeed  = [0] * 4
    MotorEnable = [0] * 4

    EncoderOffset = [None] * 4
    Encoder       = [None] * 4

    Sensor         = [None] * 4
    SensorArray    = [ [None] * 4 for i in range(4) ]
    SensorType     = [0] * 4
    SensorSettings = [ [None] * 8 for i in range(4) ]

    SensorI2CDevices = [None] * 4
    SensorI2CSpeed   = [None] * 4
    SensorI2CAddr    = [ [None] * 8 for i in range(4) ]
    SensorI2CWrite   = [ [None] * 8 for i in range(4) ]
    SensorI2CRead    = [ [None] * 8 for i in range(4) ]
    SensorI2COut     = [ [ [None] * 16 for i in range(8) ] for i in range(4) ]
    SensorI2CIn      = [ [ [None] * 16 for i in range(8) ] for i in range(4) ]
    
BrickPi = BrickPiStruct()


def BrickPiChangeAddress(OldAddr, NewAddr):
    Array[BYTE_MSG_TYPE] = MSG_TYPE_CHANGE_ADDR;
    Array[BYTE_NEW_ADDRESS] = NewAddr;
    BrickPiTx(OldAddr, 2, Array)
    res, BytesReceived, InArray = BrickPiRx(0.005000)
    if res :
        return -1
    for i in range(len(InArray)):
        Array[i] = InArray[i]
    if not (BytesReceived == 1 and Array[BYTE_MSG_TYPE] == MSG_TYPE_CHANGE_ADDR):
        return -1
    return 0

    
def GetBits( byte_offset, bit_offset, bits):
    global Bit_Offset
    result = 0
    i = bits
    while i:
        result *= 2
        result |= ((Array[(byte_offset + ((bit_offset + Bit_Offset + (i-1)) / 8))] >> ((bit_offset + Bit_Offset + (i-1)) % 8)) & 0x01)
        i -= 1
    Bit_Offset += bits
    return result


def BitsNeeded(value):
    for i in range(32):
        if not value:
            return i
        value /= 2
    return 31


def AddBits(byte_offset, bit_offset, bits, value):
    global Bit_Offset
    for i in range(bits):
        if(value & 0x01):
            Array[(byte_offset + ((bit_offset + Bit_Offset + i)/ 8))] |= (0x01 << ((bit_offset + Bit_Offset + i) % 8));
        value /=2
    Bit_Offset += bits


def BrickPiSetupSensors():
    global Array
    global Bit_Offset
    global BytesReceived
    for i in range(2):
        Array = [0] * 256
        Bit_Offset = 0
        Array[BYTE_MSG_TYPE] = MSG_TYPE_SENSOR_TYPE
        Array[BYTE_SENSOR_1_TYPE] = BrickPi.SensorType[PORT_1 + i*2 ]
        Array[BYTE_SENSOR_2_TYPE] = BrickPi.SensorType[PORT_2 + i*2 ]
        for ii in range(2):
            port = i*2 + ii
            if(Array[BYTE_SENSOR_1_TYPE + ii] == TYPE_SENSOR_I2C or Array[BYTE_SENSOR_1_TYPE + ii] == TYPE_SENSOR_I2C_9V ):
                AddBits(3,0,8,BrickPi.SensorI2CSpeed[port])

                if(BrickPi.SensorI2CDevices[port] > 8):
                    BrickPi.SensorI2CDevices[port] = 8

                if(BrickPi.SensorI2CDevices[port] == 0):
                    BrickPi.SensorI2CDevices[port] = 1

                AddBits(3,0,3, (BrickPi.SensorI2CDevices[port] - 1))

                for device in range(BrickPi.SensorI2CDevices[port]):
                    AddBits(3,0,7, (BrickPi.SensorI2CAddr[port][device] >> 1))
                    AddBits(3,0,2, BrickPi.SensorSettings[port][device])
                    if(BrickPi.SensorSettings[port][device] & BIT_I2C_SAME):
                        AddBits(3,0,4, BrickPi.SensorI2CWrite[port][device])
                        AddBits(3,0,4, BrickPi.SensorI2CRead[port][device])

                        for out_byte in range(BrickPi.SensorI2CWrite[port][device]):
                            AddBits(3,0,8, BrickPi.SensorI2COut[port][device][out_byte])

        tx_bytes = (((Bit_Offset + 7) / 8) + 3) #eq to UART_TX_BYTES
        BrickPiTx(BrickPi.Address[i], tx_bytes , Array)
        res, BytesReceived, InArray = BrickPiRx(0.500000)
        if res :
            return -1
        for i in range(len(InArray)):
            Array[i]=InArray[i]
        if not (BytesReceived ==1 and Array[BYTE_MSG_TYPE] == MSG_TYPE_SENSOR_TYPE) :
            return -1
    return 0


def BrickPiUpdateValues():
    global Array
    global Bit_Offset
    global Retried
    ret = False
    i = 0
    while i < 2 :
        if not ret:
            Retried = 0
        #Retry Communication from here, if failed

        Array = [0] * 256
        Array[BYTE_MSG_TYPE] = MSG_TYPE_VALUES
        Bit_Offset = 0

        for ii in range(2):
            port = (i * 2) + ii
            if(BrickPi.EncoderOffset[port]):
                Temp_Value = BrickPi.EncoderOffset[port]
                AddBits(1,0,1,1)
                if Temp_Value < 0 :
                    Temp_ENC_DIR = 1
                    Temp_Value *= -1
                Temp_BitsNeeded = BitsNeeded(Temp_Value) + 1
                AddBits(1,0,5, Temp_BitsNeeded)
                Temp_Value *= 2
                Temp_Value |= Temp_ENC_DIR
                AddBits(1,0, Temp_BitsNeeded, Temp_Value)
            else:
                AddBits(1,0,1,0)


        for ii in range(2):
            port = (i *2) + ii
            speed = BrickPi.MotorSpeed[port]
            direc = 0
            if speed<0 :
                direc = 1
                speed *= -1
            if speed>255:
                speed = 255
            AddBits(1,0,10,((((speed & 0xFF) << 2) | (direc << 1) | (BrickPi.MotorEnable[port] & 0x01)) & 0x3FF))


        for ii in range(2):
            port =  (i * 2) + ii
            if(BrickPi.SensorType[port] == TYPE_SENSOR_I2C or BrickPi.SensorType[port] == TYPE_SENSOR_I2C_9V):
                for device in range(BrickPi.SensorI2CDevices[port]):
                    if not (BrickPi.SensorSettings[port][device] & BIT_I2C_SAME):
                        AddBits(1,0,4, BrickPi.SensorI2CWrite[port][device])
                        AddBits(1,0,4, BrickPi.SensorI2CRead[port][device])
                        for out_byte in range(BrickPi.SensorI2CWrite[port][device]):
                            AddBits(1,0,8, BrickPi.SensorI2COut[port][device][out_byte])
                    device += 1


        tx_bytes = (((Bit_Offset + 7) / 8 ) + 1) #eq to UART_TX_BYTES
        BrickPiTx(BrickPi.Address[i], tx_bytes, Array)

        result, BytesReceived, InArray = BrickPiRx(0.007500) #check timeout
        for j in range(len(InArray)):
            Array[j]=InArray[j]
        
        if result != -2 :
            BrickPi.EncoderOffset[(i * 2) + PORT_A] = 0
            BrickPi.EncoderOffset[(i * 2) + PORT_B] = 0

        if (result or (Array[BYTE_MSG_TYPE] != MSG_TYPE_VALUES)):
            if 'DEBUG' in globals():
                if DEBUG == 1:
                    print "BrickPiRx Error :", result
            
            if Retried < 2 :
                ret = True
                Retried += 1
                #print "Retry", Retried
                continue
            else:
                if 'DEBUG' in globals():
                    if DEBUG == 1:
                        print "Retry Failed"
                return -1


        ret = False
        Bit_Offset = 0

        Temp_BitsUsed = [] 
        Temp_BitsUsed.append(GetBits(1,0,5))
        Temp_BitsUsed.append(GetBits(1,0,5))

        for ii in range(2):
            Temp_EncoderVal = GetBits(1,0, Temp_BitsUsed[ii])
            if Temp_EncoderVal & 0x01 :
                Temp_EncoderVal /= 2
                BrickPi.Encoder[ii + i*2] = Temp_EncoderVal*(-1)
            else:
                BrickPi.Encoder[ii + i*2] = Temp_EncoderVal / 2


        for ii in range(2):
            port = ii + (i * 2)
            if BrickPi.SensorType[port] == TYPE_SENSOR_TOUCH :
                BrickPi.Sensor[port] = GetBits(1,0,1)
            elif BrickPi.SensorType[port] == TYPE_SENSOR_ULTRASONIC_CONT or BrickPi.SensorType[port] == TYPE_SENSOR_ULTRASONIC_SS :
                BrickPi.Sensor[port] = GetBits(1,0,8)
            elif BrickPi.SensorType[port] == TYPE_SENSOR_COLOR_FULL:
                BrickPi.Sensor[port] = GetBits(1,0,3)
                BrickPi.SensorArray[port][INDEX_BLANK] = GetBits(1,0,10)
                BrickPi.SensorArray[port][INDEX_RED] = GetBits(1,0,10)
                BrickPi.SensorArray[port][INDEX_GREEN] = GetBits(1,0,10)
                BrickPi.SensorArray[port][INDEX_BLUE] = GetBits(1,0,10)
            elif BrickPi.SensorType[port] == TYPE_SENSOR_I2C or BrickPi.SensorType[port] == TYPE_SENSOR_I2C_9V :
                BrickPi.Sensor[port] = GetBits(1,0, BrickPi.SensorI2CDevices[port])
                for device in range(BrickPi.SensorI2CDevices[port]):
                    if (BrickPi.Sensor[port] & ( 0x01 << device)) :
                        for in_byte in range(BrickPi.SensorI2CRead[port][device]):
                            BrickPi.SensorI2CIn[port][device][in_byte] = GetBits(1,0,8)
            else:   #For all the light, color and raw sensors 
                BrickPi.Sensor[ii + (i * 2)] = GetBits(1,0,10)

        i += 1
    return 0


def BrickPiSetup():
    if ser.isOpen():
        return -1
    ser.open()
    if not ser.isOpen():
        return -1
    return 0

	
def BrickPiTx(dest, ByteCount, OutArray):
    tx_buffer = ''
    tx_buffer+=chr(dest)
    tx_buffer+=chr((dest+ByteCount+sum(OutArray[:ByteCount]))%256)
    tx_buffer+=chr(ByteCount)
    for i in OutArray[:ByteCount]:
        tx_buffer+=chr(i)
    ser.write(tx_buffer)


def BrickPiRx(timeout):
    rx_buffer = ''
    ser.timeout=0
    ot = time.time() 

    while( ser.inWaiting() <= 0):
        if time.time() - ot >= timeout : 
            return -2, 0 , []
    
    if not ser.isOpen():
        return -1, 0 , []
    
    try:
        while ser.inWaiting():
            rx_buffer += ( ser.read(ser.inWaiting()) )
            #time.sleep(.000075)
    except:
        return -1, 0 , []
    
    RxBytes=len(rx_buffer)
    
    if RxBytes < 2 :
        return -4, 0 , []

    if RxBytes < ord(rx_buffer[1])+2 :
        return -6, 0 , []

    CheckSum = 0 
    for i in rx_buffer[1:]:
        CheckSum += ord(i)

    InArray = []
    for i in rx_buffer[2:]:
        InArray.append(ord(i))
    if (CheckSum % 256) != ord(rx_buffer[0]) : #Checksum equals sum(InArray)+len(InArray)
        return -5, 0 , []

    InBytes = RxBytes - 2

    return 0, InBytes, InArray 
