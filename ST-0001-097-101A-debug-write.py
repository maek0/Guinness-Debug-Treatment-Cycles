import sys
import subprocess
import time

tool_version = "ST-0001-097-101A"

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

proceed = input("\nAttempting to uninstall the 'serial' module if installed. The script will not work with this module installed - proceed? (Y/n):  ")
if proceed == "y" or proceed == "Y":
    uninstall('serial')
else:
    print("\nThe script will not work without verifying if 'serial' is not installed. Exiting script...\n")
    time.sleep(3)
    exit()

try:
    import serial
except ImportError:
    print("\nThe required Python module 'pyserial' is not installed, installing now...\n")
    time.sleep(1)
    install('pyserial')
    import serial

try:
    from tqdm import tqdm
except ImportError:
    print("\nThe required Python module 'tqdm' is not installed, installing now...\n")
    time.sleep(1)
    install('tqdm')
    from tqdm import tqdm

try:
    import numpy as np
except ImportError:
    print("\nThe required Python module 'numpy' is not installed, installing now...\n")
    time.sleep(1)
    install('numpy')
    import numpy as np

errormsg = "\nCan't write to the serial port, check the system's connections and the input parameters. Error type: "
errormsgEnd = "\nLost connection with the machine. Error type: "

def windowClose():
    time.sleep(5)
    f.close()
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

def catchError(serial, functionstartTime,count):
    errorCase = serial.readline().decode().startswith("FSM Task: Enter STATE_ERROR")
    if errorCase:
        errorTime = time.time()
        printLog("\nGenerator threw an error at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        printLog(str(count)+' complete treatment cycle(s) ran during this time.')
        windowClose()
        
def catchFault(serial, functionstartTime,count):
    faultCase = serial.readline().decode().startswith("FSM Task: Recv Fault Message:")
    if faultCase:
        noconnection = time.time()
        printLog("\nGenerator threw a fault at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        printLog(str(count)+' complete treatment cycle(s) ran during this time.')
        windowClose()

def verifyStart(serial, treatTime):
    output = serial.readline().decode().startswith("FSM Task:")
    if not output:
        treatTimeNew = time.time()
        serial.write("start\r".encode())
        treatTime = verifyStart(serial, treatTimeNew)
        time.sleep(0.2)
    else:
        treatTimeNew = treatTime
    return treatTimeNew
    
def functionStop(functionstartTime, count):
    functionstop = time.time()
    delta = ((functionstop-functionstartTime)/60)/60  # hours
    if count >= 0:
        i = count
    else:
        i = 0
        
    printLog("\nThe script ran for {:0.3f} hours.".format(delta))
    printLog(str(i)+' complete treatment cycle(s) ran during this time.')
    print("\nSee ",debug_filename,"for record of output printed to terminal.")
    windowClose()
    
def errorHandle(message,name):
    printLog(message,name)
    f.close()
    print("\nExiting...")
    time.sleep(5)
    exit()
    
def readWrite(serial,functionstartTime,i):
    output = serial.readline()
    f.write(output)
    
    if not output:
        stoptime = time.time()
        printLog("\nError: The generator stopped sending data at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionStop(functionstartTime,i)

def catchStop(serial, toc, i):
    if serial.readline().decode().startswith("Treatment Terminated Early..."):
        printLog("\nThe treatment cycle was stopped early. Only {:.2f} seconds had elapsed instead of 240.\nThis cycle will not count as a completed treatment cycle.\n".format(toc))
        newi = i -1
    elif serial.readline().decode().startswith("FSM Task: recieved button index 11"):
        printLog("\nThe treatment cycle was stopped early. Only {:.2f} seconds had elapsed instead of 240.\nThis cycle will not count as a completed treatment cycle.\n".format(toc))
        newi = i -1
    else:
        newi = i
        
    if newi < 0:
        newi = 0
        
    return newi

COM = input("\nEnter the COM number of the Guinness USB Debug Cable (AT-0001-656) in use: ")
if COM == "COM*":
    COMX = COM
else:
    COMX = str('COM'+COM)

name = input("Enter the file name that the serial data will be writtent to: ")
if name == "*.csv":
    filename = name
else:
    filename = str(name+'.csv')
    
debug_filename = str(name+"_terminalPrint.txt")
buffer = float(input("Enter the (nonzero) number of minutes (e.g., 62 or 0.5) to wait between applied treatment cycles: "))
if buffer == 0.0:
    printLog("\nError: The timer interval between treatment cycles must be above 0 minutes.")
    windowClose()

volt = str(input("Enter the voltage setpoint (integer in the range [0, 150]) for the treatment cycles to run at: "))
if volt == "*-*" or float(volt)>150 or volt == "*.*":
    printLog("\nError: The voltage setpoint must be an integer in the range [0, 150].")
    windowClose()
    
limit = str(input("Enter the number of treatment cycles to run (Note: the script will stop after 18,000 cycles with no intervention if a number isn't entered): "))
try:
    int(limit)
except ValueError:
    limit = 18000
except TypeError:
    limit = 18000
except IndexError:
    limit = 18000

tv = str("t_v "+volt+"\r")

f = open(filename,"ab")


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
    print("A SerialException occurred.\nReinstalling Python module 'pyserial' to ensure compatibility with script...\n")
    time.sleep(1)
    reinstall('pyserial')
    try:
        ser = serial.Serial(
            port=COMX,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE
        )
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
print("\n")
printLog("----- ",tool_version,"script started at", time.strftime("%b %d %Y %H:%M:%S")," -----")

output = ""

if int(limit)<18000:
    printLog("\nOpening serial connection with the following parameters:\n   COM Port: {}\n   Logging to File: {}\n   {} minutes between treatment cycles\n   Voltage Setpoint: {}V\n   Limited to {} treatment cycles".format(COMX,filename,buffer,volt,limit))
else:
    printLog("\nOpening serial connection with the following parameters:\n   COM Port: {}\n   Logging to File: {}\n   {} minutes between treatment cycles\n   Voltage Setpoint: {}V".format(COMX,filename,buffer,volt))

time.sleep(0.5)
printLog("\nPress CTRL+C in the terminal to stop the script at any time.\n")
time.sleep(0.5)

stat = ser.is_open
ser.timeout = 1.0
heard = False

for i in tqdm(range(10),"Verifying communication"):
    for j in range(10):
        ser.write("test\r".encode())
        output = ser.readline().decode().startswith("Test")
        if output:
            heard = True
        time.sleep(0.1)

if not heard:
    printLog("\nGenerator did not acknowledge the test command. Power cycle the generator and restart the script")
    
    print("\nSee ",debug_filename,"for record of output printed to terminal.")
    windowClose()
print("\n")
i = 0
hold = int(np.ceil(buffer*60))
cycleLength = 242   # 4 minutes +2 second for treatment cycle
# note: extra 2 seconds compensates for the 2s of sleep totalled between generator commands

timerstart = time.time()

try:
    while i <= (int(limit)-1):
        if stat == True:
            stat = ser.is_open
            readWrite(ser,functionstart,i)
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
                
                catchError(ser, functionstart,i)
                catchFault(ser, functionstart,i)
                i = catchStop(ser, toc, i)
                
                treatTime = verifyStart(ser,treatTime)
            
                while toc>=hold and toc<=int(hold+cycleLength):
                    stat = ser.is_open
                    
                    if stat == False:
                        noconnection = time.time()
                        printLog("\nLost connection with the machine at", time.strftime("%b %d %Y %H:%M:%S"))
                        functionStop(functionstart,i)
                        
                    readWrite(ser,functionstart,i)
                    
                    catchError(ser, functionstart,i)
                    catchFault(ser, functionstart,i)
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
            functionStop(functionstart,i)

except KeyboardInterrupt:
    manualstop = time.time()
    printLog("\nScript stopped manually at ", time.strftime("%b %d %Y %H:%M:%S"))
    ser.write("stop\r".encode())
except ValueError as e:
    printLog(errormsgEnd,type(e))
    ser.write("stop\r".encode())
except TimeoutError as e:
    printLog(errormsgEnd,type(e))
    ser.write("stop\r".encode())
except TypeError as e:
    printLog(errormsgEnd,type(e))
    ser.write("stop\r".encode())
except IndexError as e:
    printLog(errormsgEnd,type(e))
    ser.write("stop\r".encode())
except serial.SerialException as e:
    printLog(errormsgEnd,type(e))
except PermissionError as e:
    printLog("\n",filename,"could not be accessed. Error type: ",type(e))
    ser.write("stop\r".encode())


if int(limit)<18000:
    functionstop = time.time()
    delta = ((functionstop-functionstart)/60)/60  # hours
    
    ser.write("reset\r".encode())
    printLog(str(i)+' complete treatment cycle(s) ran during this time. The script will continue to write generator debug data to file until the window is closed.')
    
    try:
        while True:
            readWrite(ser,functionstart,i)
    except KeyboardInterrupt:
        manualstop = time.time()
        printLog("\nScript stopped manually at ", time.strftime("%b %d %Y %H:%M:%S"))
        windowClose()
        functionStop(functionstart,i)
else:
    functionStop(functionstart,i)