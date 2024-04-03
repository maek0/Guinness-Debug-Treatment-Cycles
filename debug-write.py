import serial
import time
import threading

COM = input("Enter the COM number (e.g., '5', not 'COM5') of the Guinness USB Debug Cable (AT-0001-656) in use: ")

COMX = str('COM'+COM)

filename = str(input("Enter the file name (e.g., 'fileName', not 'fileName.txt') that the serial data will be writtent to: ")+'.txt')
f = open(file=filename,mode='x')
f.close()

ser = serial.Serial(
    port=COMX,
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE
)

functionstart = time.localtime()

output = ""

while 1:
    # log serial output:
    output = ser.readline()
    f = open(file=filename,mode='a')
    f.write(str(output))
    f.close()


functionstop = time.localtime()
delta = functionstop-functionstart
print('The function ran for '+ delta)