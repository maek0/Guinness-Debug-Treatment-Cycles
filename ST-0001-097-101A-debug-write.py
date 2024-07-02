import sys
import subprocess
import time

tool_version = "ST-0001-097-101A"

# function to install package, just reduces repeated commands in the script
def install(package):
    subprocess.check_call([sys.executable,"-m","pip","install",package])

# function to force a package to reinstall, just reduces repeated commands in the script
def reinstall(package):
    subprocess.check_call([sys.executable,"-m","pip","install","--upgrade","--force-reinstall",package])

# function to uninstall package, just reduces repeated commands in the script
def uninstall(package):
    subprocess.check_call([sys.executable,"-m","pip","uninstall",package])

# function to print to both the log file AND the terminal
def printLog(*args, **kwargs):
    print(*args, **kwargs)
    with open(debug_filename,'a') as file:
        print(*args, **kwargs, file=file)

# see if the serial module is installed, if not = install
# this module allows/handles serial communication
try:
    import serial
except ImportError:
    print("\nThe required Python module 'pyserial' is not installed, installing now...\n")
    time.sleep(1)
    install('pyserial')
    import serial

# see if the tqdm module is installed, if not = install
# this module is just used for loading bar
try:
    from tqdm import tqdm
except ImportError:
    print("\nThe required Python module 'tqdm' is not installed, installing now...\n")
    time.sleep(1)
    install('tqdm')
    from tqdm import tqdm

# see if the numpy module is installed, if not = install
# this module is used for math and stuff :)
try:
    import numpy as np
except ImportError:
    print("\nThe required Python module 'numpy' is not installed, installing now...\n")
    time.sleep(1)
    install('numpy')
    import numpy as np

# standardized, generic error message
errormsg = "\nCan't write to the serial port, check the system's connections and the input parameters. Error type: "
errormsgEnd = "\nLost connection with the machine. Error type: "

# function to close script window (when script is being run independently - i.e., not in VSCode), just reduces repeated commands in the script
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

# function to check if the Guinness generator started the treatment cycle
def verifyStart(serial):
    heard = False
    output = serial.readline().decode().startswith("FSM Task:")
    while not heard:
        time.sleep(0.1)
        ser.write("start\r".encode())
        output = ser.readline().decode().startswith("FSM Task:")
        if output:
            heard = True
            treatTimeNew = time.time()
        time.sleep(0.1)
        # if not output:
        #     treatTimeNew = time.time()
        #     serial.write("start\r".encode())
        #     treatTimeNew = verifyStart(serial, treatTimeNew)
        #     time.sleep(0.2)
    return treatTimeNew

# function to report parameters of the script runtime and the number of completed treatment cycles that ran
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

# function to report encountered errors with specified error message both in terminal and in log
def errorHandle(message,name):
    printLog(message,name)
    f.close()
    print("\nExiting...")
    time.sleep(5)
    exit()

# IMPLEMENTED: If error --> don't attempt to start any more treatment cycles, report completed number of treatment cycles, keep logging [POSSIBLY (successfully implemented), resume treatment cycles if error is acknowledged]
def readWrite(serial,functionstartTime,count,errorCase):
    output = serial.readline()
    f.write(output)
    skip = False
    
    if not output:
        stoptime = time.time()
        printLog("\nError: The generator stopped sending data at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionStop(functionstartTime,count)
    elif output.decode().startswith("FSM Task: Recv Fault Message:"):
        noconnection = time.time()
        functionCode = str(output.decode())[-6:-3]
        printLog(f"\nGenerator threw fault F{functionCode} at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        printLog(str(count)+' complete treatment cycle(s) ran during this time.')
        windowClose()
    elif output.decode().startswith("FSM Task: Recv Error Message"):
        errorTime = time.time()
        errorCode = str(output.decode())[-6:-3]
        printLog(f"\nGenerator threw error E{errorCode} at", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        printLog(str(count)+' complete treatment cycle(s) ran during this time. The script will continue to write generator debug data to file unless the window is closed. The script will resume treatment cycles if the error is cleared.')
        errorCase = True
    elif output.decode().startswith("FSM Task: Exit STATE_ERROR"):
        errorClear = time.time()
        printLog("\nGenerator exited Error State at", time.strftime("%b %d %Y %H:%M:%S"))
        printLog("Resuming treatment cycles.\n")
        errorCase = False
    elif output.decode().startswith("Treatment Terminated Early..."):
        printLog("\nThe treatment cycle was stopped early. Only {:.2f} seconds had elapsed instead of 240.\nThis cycle will not count as a completed treatment cycle.\n".format(toc))
        skip = True
        
    return skip, errorCase

# function to print only to the log, NOT the terminal
def onlyLog(serial,functionstartTime,count):
    output = serial.readline()
    f.write(output)
    
    if not output:
        stoptime = time.time()
        printLog("\nError: The generator stopped sending data at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionStop(functionstartTime,count)
    elif output.decode().startswith("FSM Task: Recv Fault Message:"):
        noconnection = time.time()
        printLog("\nGenerator threw a fault at ", time.strftime("%b %d %Y %H:%M:%S"))
        functionstop = time.time()
        delta = ((functionstop-functionstartTime)/60)/60  # hours
        printLog("\nThe function ran for {:0.3f} hours.".format(delta))
        printLog(str(count)+' complete treatment cycle(s) ran during this time.\n')
        windowClose()

# prompt user to enter COM number of the debug cable (able to handle both "X" and "COMX", where X is the COM number)
COM = input("\nEnter the COM number of the Guinness USB Debug Cable (AT-0001-656) in use: ")
if COM == "COM*":
    COMX = COM
else:
    COMX = str('COM'+COM)

# prompt user to enter name of the file where data is to be written
name = input("Enter the file name of the .csv that the serial data will be writtent to: ")
if name == "*.csv":
    filename = name
else:
    filename = str(name+'.csv')
    
debug_filename = str(name+"_terminalPrint.txt")

# prompt user to enter number of minutes between treatment cycles. This allows treatment cycles to be started immediately after
# 0.1 should generally be the minimum input value (6 seconds), any shorter than this and the commands might start to overlap and the generator might get unhappy (throw fault)
buffer = float(input("Enter the (nonzero) number of minutes (e.g., 62 or 0.5) to wait between applied treatment cycles: "))
if buffer == 0.0:
    printLog("\nError: The timer interval between treatment cycles must be above 0 minutes.")
    windowClose()

# prompt user to enter treatment voltage setpoint - NO DECIMALS.
volt = str(input("Enter the voltage setpoint (integer in the range [0, 150]) for the treatment cycles to run at: "))
if volt == "*-*" or float(volt)>150 or volt == "*.*":
    printLog("\nError: The voltage setpoint must be an integer in the range [0, 150].")
    windowClose()

# prompt user to enter a finite number of treatment cycles to be run 
# if an integer is entered, it overrides the default of 18,000 cycles. 18,000 default comes from the service life requirement GUIN-mSYSREQ-188
limit = str(input("Enter the number of treatment cycles to run (Note: the script will stop after 18,000 cycles with no intervention if a number isn't entered): "))
try:
    int(limit)
except ValueError:
    limit = 18000
except TypeError:
    limit = 18000
except IndexError:
    limit = 18000

# command variable to set Generator's treatment voltage
tv = str("t_v "+volt+"\r")

# open the specified file - the file will remain open until script stops running.
f = open(filename,"ab")

# attempt serial communication, includes error handling for specific encountered errors
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
    print("A SerialException occurred.\nAttempting to uninstall Python module 'serial' and reinstall Python module 'pyserial' to ensure compatibility with script...\n")
    time.sleep(1)
    uninstall('serial')
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

# get current time, this will be used as the script's start time
functionstart = time.time()
print("\n")

# log print header
printLog("----- ",tool_version,"script started at", time.strftime("%b %d %Y %H:%M:%S")," -----")

output = ""

# summary output of the user-input parameters
if int(limit)<18000:
    printLog("\nOpening serial connection with the following parameters:\n   COM Port: {}\n   Logging to File: {}\n   {} minutes between treatment cycles\n   Voltage Setpoint: {}V\n   Limited to {} treatment cycles".format(COMX,filename,buffer,volt,limit))
else:
    printLog("\nOpening serial connection with the following parameters:\n   COM Port: {}\n   Logging to File: {}\n   {} minutes between treatment cycles\n   Voltage Setpoint: {}V\n   No treatment cycle limit.".format(COMX,filename,buffer,volt))

time.sleep(0.5)
printLog("\nPress CTRL+C in the terminal to stop the script at any time.\n")
time.sleep(0.5)

# serial settings
stat = ser.is_open
ser.timeout = 1.0

# flag to indicate if communication with the generator has been confirmed
heard = False

for i in tqdm(range(10),"Verifying communication"):
    for j in range(2):
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

# initialize count of the number of treatment cycles that have been run
i = int(0)

# variable that translates the input "buffer" to seconds, allowing use in the script 
hold = int(np.ceil(buffer*60))

cycleLength = 241   # 4 minutes +1 second for treatment cycle
# note: extra 1 seconds compensates for the 1s of sleep totalled between generator commands

timerstart = time.time()

# flag for error active
error = False

try:
    while i <= (int(limit)-1):
        if stat == True:
            skip = False
            stat = ser.is_open
            _, error = readWrite(ser,functionstart,i,error)
            while error:
                _, error = readWrite(ser,functionstart,i,error)
                timerstart = time.time()
            tic = time.time()
            toc = tic-timerstart
            
            # code block for when treatment cycle should be started
            if toc>=hold:
                time.sleep(0.25)
                ser.write("reset\r".encode())
                time.sleep(0.25)
                ser.write("treatment\r".encode())
                time.sleep(0.25)
                ser.write(tv.encode())
                time.sleep(0.15)
                
                # when was the treatment confirmed to start?
                treatTime = verifyStart(ser)
                printLog('Treatment cycle #{} starting at'.format(i+1), time.strftime("%b %d %Y %H:%M:%S"),' ...')

                # code block fro when treatment cycle should be running
                while toc>=hold and toc<=int(hold+cycleLength):
                    skip, error = readWrite(ser,functionstart,i,error)
                    
                    # "skip" flag notifies the script if the treatment cycle ended early (stop button is pressed)
                    if skip:
                        timerstart = time.time()
                        # jump out of this while loop and restart the countdown to treatment
                    
                    # "error" flag notifies the script if the generator encounters an error
                    while error:
                        skip, error = readWrite(ser,functionstart,i,error)
                        timerstart = time.time()
                        skip = True
                        # monitor for if the error is cleared, if it ever is - the treatment counter has already been restarted
                        # skip is being forced as True since this error catch is within an assumed treatment cycle - if an error was caught in this code block, a treatment cycle would not have completed
                    
                    tic = time.time()
                    toc = tic-timerstart
                
                if skip:
                    pass
                    # we didn't complete a treatment cycle, don't increment cycle count
                else:
                    i = i +1
                    # we DID complete a treatment cycle, increment cycle count
                
                # restart the countdown to treatment:
                timerstart = time.time()
                tic = time.time()
                toc = tic-timerstart
        else:
            noconnection = time.time()
            printLog("\nLost connection with the machine at", time.strftime("%b %d %Y %H:%M:%S"))
            functionStop(functionstart,i)

# handling for identified script errors
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

# if the specified number of treatment cycles (assumed < 18k) is reached, keep logging until user intervention or generator dies
if int(limit)<18000:
    functionstop = time.time()
    delta = ((functionstop-functionstart)/60)/60  # hours
    
    ser.write("reset\r".encode())
    printLog(str(i)+' complete treatment cycle(s) ran during {:.3f} hours. The script will continue to write generator debug data to file until the window is closed.'.format(delta))
    
    try:
        while True:
            onlyLog(ser,functionstart,i)
    except KeyboardInterrupt:
        manualstop = time.time()
        printLog("\nScript stopped manually at ", time.strftime("%b %d %Y %H:%M:%S"))
        windowClose()
        functionStop(functionstart,i)
# if 18,000 treatments ran, logging WILL stop. This can be changed, but currently I don't see much value in continuing to log (the log for the service life test case will already be massive)
# POTENTIAL FUTURE PROBLEM - I don't know what will happen with the service life test log as it keeps building. As far as I currently understand, we CANNOT limit the readwrite frequency to limit data intake - we WILL miss important generator output that will inform the script's decisions.
else:
    functionStop(functionstart,i)