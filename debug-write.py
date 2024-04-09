import sys
import subprocess
import time

def install(package):
    subprocess.check_call([sys.executable,"-m","pip","install",package])

try:
    import serial
except ImportError:
    print("The required Python module 'serial' is not installed, installing now...")
    time.sleep(0.5)
    install('pyserial')

try:
    import numpy as np
except ImportError:
    print("The required Python module 'numpy' is not installed, installing now...")
    time.sleep(0.5)
    install('numpy')

COM = input("Enter the COM number (e.g., '5', not 'COM5') of the Guinness USB Debug Cable (AT-0001-656) in use: ")

COMX = str('COM'+COM)

name = input("Enter the file name (e.g., 'fileName', not 'fileName.csv') that the serial data will be writtent to: ")
filename = str(name+'.csv')
debug_filename = str(name+"_terminalPrint.txt")
buffer = float(input("Enter the (nonzero) number of minutes (e.g., 62 or 0.5) to wait between applied treatment cycles: "))
volt = str(input("Enter the voltage setpoint (integer in the range [0, 150]) for the treatment cycles to run at: "))
tv = str("t_v "+volt+"\r")

def printLog(*args, **kwargs):
    print(*args, **kwargs)
    with open(debug_filename,'a') as file:
        print(*args, **kwargs, file=file)

errormsg = "\nCan't write to the serial port, check the system's connections and the input parameters. Error type: "

try:
    ser = serial.Serial(
        port=COMX,
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        parity=serial.PARITY_NONE
    )
except FileNotFoundError as e:
    printLog(errormsg,type(e))
    sys.exit()
except serial.SerialException as e:
    printLog(errormsg,type(e))
    sys.exit()
except ValueError as e:
    printLog(errormsg,type(e))
    sys.exit()
except TimeoutError as e:
    printLog(errormsg,type(e))
    sys.exit()
except TypeError as e:
    printLog(errormsg,type(e))
    sys.exit()
except IndexError as e:
    printLog(errormsg,type(e))
    sys.exit()
    
functionstart = time.time()
printLog("\nScript started at ", time.strftime("%b %d %Y %H:%M:%S"))


output = ""

printLog("\nOpening serial connection with the following parameters:\n   COM Port: {}\n   Logging to File: {}\n   {} minutes between treatment cycles\n   Voltage Setpoint: {}V".format(COMX,filename,buffer,volt))
time.sleep(0.5)
printLog("\nPress CTRL+C in the terminal to stop the script at any time.\n")
time.sleep(0.5)

stat = ser.is_open
ser.write("test\r".encode())
    
i = 0
hold = int(np.ceil(buffer*60))
cycleLength = 242   # 4 minutes +2 second for treatment cycle
# note: extra 2 seconds compensates for the 2s of sleep totalled between commands

timerstart = time.time()

try:
    while i < 18001:
        while stat == True:
            stat = ser.is_open
            output = ser.readline()
            f = open(filename,"ab")
            f.write(output)
            f.close()
            tic = time.time()
            toc = tic-timerstart

            if toc>=hold:
                printLog('Treatment cycle #'+str(i+1)+' starting...')
                time.sleep(0.5)
                ser.write("reset\r".encode())
                time.sleep(0.5)
                ser.write("treatment\r".encode())
                time.sleep(0.5)
                ser.write(tv.encode())
                time.sleep(0.5)
                ser.write("start\r".encode())

                while toc>=hold and toc<=int(hold+cycleLength):
                    stat = ser.is_open
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

except KeyboardInterrupt:
    manualstop = time.time()
    printLog("\nScript stopped manually at ", time.strftime("%b %d %Y %H:%M:%S"))
    pass
except ValueError as e:
    printLog("\nSomething went wrong, check the system's connections and setup. Error type: ",type(e))
except TimeoutError as e:
    printLog("\nSomething went wrong, check the system's connections and setup. Error type: ",type(e))
except TypeError as e:
    printLog("\nSomething went wrong, check the system's connections and setup. Error type: ",type(e))
except IndexError as e:
    printLog("\nSomething went wrong, check the system's connections and setup. Error type: ",type(e))
    
functionstop = time.time()
delta = ((functionstop-functionstart)/60)/60  # hours
printLog("\nThe function ran for {:0.3f} hours.".format(delta))
printLog(str(i)+' complete treatment cycle(s) ran during this time.')
print("\nSee ",debug_filename,"for record of output printed to terminal.")
time.sleep(10)
print("\nWindow closing in...")
print("5...")
time.sleep(1)
print("4...")
time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)