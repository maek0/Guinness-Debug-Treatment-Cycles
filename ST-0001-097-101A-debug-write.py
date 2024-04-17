import sys
import subprocess
import time

def install(package):
    subprocess.check_call([sys.executable,"-m","pip","install",package])
    
def reinstall(package):
    subprocess.check_call([sys.executable,"-m","pip","install","--upgrade","--force-reinstall",package])

def uninstall(package):
    subprocess.check_call([sys.executable,"-m","pip","uninstall",package])

def printLog(*args, **kwargs):
    print(*args, **kwargs)
    with open(debug_filename,'a') as file:
        print(*args, **kwargs, file=file)
        
# try:
#     proceed = input("\nAttempting to uninstall the 'serial' module if installed. The script will not work with this module installed - proceed? (Y/n):  ")
#     if proceed == "y" or "Y":
#         uninstall('serial')
#     else:
#         print("\nThe script will not work without verifying if 'serial' is not installed. Exiting script...")
#         time.sleep(3)
#         exit()
#     print("(Re)installing Python module 'pyserial' to ensure compatibility with script...")
#     time.sleep(1)
#     reinstall('pyserial')
#     import serial
# except ImportError:
#     print("The required Python module 'pyserial' is not installed, installing now...")
#     time.sleep(1)
#     install('pyserial')
#     import serial
import serial

try:
    from tqdm import tqdm
except ImportError:
    print("The required Python module 'tqdm' is not installed, installing now...")
    time.sleep(1)
    install('tqdp')

try:
    import numpy as np
except ImportError:
    print("The required Python module 'numpy' is not installed, installing now...")
    time.sleep(1)
    install('numpy')

def catchError(serial, functionstartTime):
    errorCase = serial.readline().decode().startswith("FSM Task: Enter STATE_ERROR")
    if errorCase:
        errorTime = time.time()
        printLog("\nGenerator threw an error at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        time.sleep(5)
        exit()
        
def catchFault(serial, functionstartTime):
    faultCase = serial.readline().decode().startswith("FSM Task: Recv Fault Message:")
    if faultCase:
        noconnection = time.time()
        printLog("\nGenerator threw a fault at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        time.sleep(5)
        exit()

def verifyStart(serial, treatTime):
    output = serial.readline().decode().startswith("FSM Task:")
    if not output:
        treatTimeNew = time.time()
        serial.write("start\r".encode())
        treatTime = verifyStart(serial, treatTimeNew)
    else:
        treatTimeNew = treatTime
    return treatTimeNew

def windowClose():
    time.sleep(5)
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
    exit()
    
def functionStop(functionstartTime):
    functionstop = time.time()
    delta = ((functionstop-functionstartTime)/60)/60  # hours
    printLog("\nThe script ran for {:0.3f} hours.".format(delta))
    printLog(str(i)+' complete treatment cycle(s) ran during this time.')
    print("\nSee ",debug_filename,"for record of output printed to terminal.")
    windowClose()
    
def errorHandle(message,name):
    printLog(message,name)
    print("Exiting...")
    time.sleep(5)
    exit()
    
def readWrite(filename,serial,functionstartTime):
    output = serial.readline()
    f = open(filename,"ab")
    f.write(output)
    f.close()
    
    if not output:
        stoptime = time.time()
        printLog("The generator stopped sending data at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionStop(functionstartTime)

def catchStop(serial, toc, i):
    output = serial.readline().decode().startswith("Treatment Terminated Early")
    if output:
        printLog("\nThe treatment cycle was stopped early. Only {:.2f} seconds had elapsed instead of 240.\nThis cycle will not count as a completed treatment cycle.".format(toc))
        newi = i -1
    else:
        newi = i
    return newi

COM = input("Enter the COM number (e.g., '5', not 'COM5') of the Guinness USB Debug Cable (AT-0001-656) in use: ")

COMX = str('COM'+COM)

name = input("Enter the file name (e.g., 'fileName', not 'fileName.csv') that the serial data will be writtent to: ")
filename = str(name+'.csv')
debug_filename = str(name+"_terminalPrint.txt")
buffer = float(input("Enter the (nonzero) number of minutes (e.g., 62 or 0.5) to wait between applied treatment cycles: "))
volt = str(input("Enter the voltage setpoint (integer in the range [0, 150]) for the treatment cycles to run at: "))
tv = str("t_v "+volt+"\r")

errormsg = "\nCan't write to the serial port, check the system's connections and the input parameters. Error type: "
errormsgEnd = "\nLost connection with the machine. Error type: "

try:
    ser = serial.Serial(
        port=COMX,
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        parity=serial.PARITY_NONE
    )
except FileNotFoundError as e:
    errorHandle(errormsg,type(e))
except serial.SerialException as e:
    errorHandle(errormsg,type(e))
except ValueError as e:
    errorHandle(errormsg,type(e))
except TimeoutError as e:
    errorHandle(errormsg,type(e))
except TypeError as e:
    errorHandle(errormsg,type(e))
except IndexError as e:
    errorHandle(errormsg,type(e))
    
functionstart = time.time()
printLog("\nScript started at ", time.strftime("%b %d %Y %H:%M:%S"))

output = ""

printLog("\nOpening serial connection with the following parameters:\n   COM Port: {}\n   Logging to File: {}\n   {} minutes between treatment cycles\n   Voltage Setpoint: {}V".format(COMX,filename,buffer,volt))
time.sleep(0.5)
printLog("\nPress CTRL+C in the terminal to stop the script at any time.\n")
time.sleep(0.5)

stat = ser.is_open
ser.timeout = 1.0
heard = False

for i in tqdm(range(10),"Verifying communication"):
    ser.write("test\r".encode())
    for j in range(10):
        output = ser.readline().decode().startswith("Test")
        if output:
            heard = True
    time.sleep(0.1)

if not heard:
    printLog("\nGenerator did not acknowledge the test command. Power cycle the generator and restart the script")
    
    print("\nSee ",debug_filename,"for record of output printed to terminal.")
    windowClose()

i = 0
hold = int(np.ceil(buffer*60))
cycleLength = 242   # 4 minutes +2 second for treatment cycle
# note: extra 2 seconds compensates for the 2s of sleep totalled between generator commands

timerstart = time.time()

try:
    while i < 18001:
        if stat == True:
            stat = ser.is_open
            readWrite(filename,ser,functionstart)
            tic = time.time()
            toc = tic-timerstart

            if toc>=hold:
                treatTime = time.time()
                printLog('Treatment cycle #'+str(i+1)+' starting at', time.strftime("%b %d %Y %H:%M:%S"),' ...')
                time.sleep(0.5)
                ser.write("reset\r".encode())
                time.sleep(0.5)
                ser.write("treatment\r".encode())
                time.sleep(0.5)
                ser.write(tv.encode())
                time.sleep(0.5)
                ser.write("start\r".encode())
                
                catchError(ser, functionstart)
                catchFault(ser, functionstart)
                
                treatTime = verifyStart(ser,treatTime)
            
                while toc>=hold and toc<=int(hold+cycleLength):
                    stat = ser.is_open
                    
                    if stat == False:
                        noconnection = time.time()
                        printLog("\nLost connection with the machine at", time.strftime("%b %d %Y %H:%M:%S"))
                        functionStop(functionstart)
                        
                    readWrite(filename,ser,functionstart)
                    
                    catchError(ser, functionstart)
                    catchFault(ser, functionstart)
                    i = catchStop(ser, toc, i)
                    
                    tic = time.time()
                    toc = tic-timerstart
                
                i = i+1
                timerstart = time.time()
                tic = time.time()
                toc = tic-timerstart
        else:
            noconnection = time.time()
            printLog("\nLost connection with the machine at", time.strftime("%b %d %Y %H:%M:%S"))
            functionStop(functionstart)

except KeyboardInterrupt:
    manualstop = time.time()
    printLog("\nScript stopped manually at ", time.strftime("%b %d %Y %H:%M:%S"))
    pass
except ValueError as e:
    printLog(errormsgEnd,type(e))
except TimeoutError as e:
    printLog(errormsgEnd,type(e))
except TypeError as e:
    printLog(errormsgEnd,type(e))
except IndexError as e:
    printLog(errormsgEnd,type(e))
except serial.SerialException as e:
    printLog(errormsgEnd,type(e))
except PermissionError as e:
    printLog("\n",filename,"could not be accessed. Error type: ",type(e))
    
functionStop(functionstart)