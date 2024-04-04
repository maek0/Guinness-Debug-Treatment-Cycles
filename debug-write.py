import serial
import time
import csv

COM = input("Enter the COM number (e.g., '5', not 'COM5') of the Guinness USB Debug Cable (AT-0001-656) in use: ")

COMX = str('COM'+COM)

filename = str(input("Enter the file name (e.g., 'fileName', not 'fileName.csv') that the serial data will be writtent to: ")+'.csv')
# print(filename)

buffer = input("Enter the number of minutes to wait between applied treatment cycles: ")

ser = serial.Serial(
    port=COMX,
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE
)

functionstart = time.time()
timerstart = time.time()

output = ""

print("Opening serial connection to "+COMX+".")
ser.write("test\r".encode())

i = 0

stat = ser.is_open

while stat == True:
    # log serial output:
    output = ser.readline()
    f = open(filename,"ab")
    f.write(output)
    f.close()
    tic = time.time()
    toc = tic-timerstart
    # print(toc)

    if toc>=5:
        print('Treatment cycle #'+str(i+1)+' starting...')
        time.sleep(0.5)
        ser.write("reset\r".encode())
        time.sleep(0.5)
        ser.write("treatment\r".encode())
        time.sleep(0.5)
        ser.write("t_v 150\r".encode())
        time.sleep(0.5)
        ser.write("start\r".encode())

        while toc>=245 and toc<=492:
            output = ser.readline()
            f = open(filename,"ab")
            f.write(output)
            f.close()
            tic = time.time()
            toc = tic-timerstart
        
        i = i+1
        timerstart = time.time()
        tic = time.time()
        toc = tic-timerstart

    if input=='q':
        break

functionstop = time.time()
delta = functionstop-functionstart
print('The function ran for '+ delta + '.')
print(str(i)+' complete treatment cycles were run.')