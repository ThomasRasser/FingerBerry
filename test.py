import time
from pyfingerprint.pyfingerprint import PyFingerprint

# Try to initialize the sensor
try:
    # Adjust the port and baudrate as needed
    f = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)
    
    if f.verifyPassword():
        print('Successfully connected to the sensor!')
    else:
        print('The given fingerprint sensor password is wrong!')
        
    # Get sensor parameters
    print(f'Sensor capacity: {f.getStorageCapacity()}')
    print(f'Templates in memory: {f.getTemplateCount()}')
    
except Exception as e:
    print(f'Error: {e}')
    print('The fingerprint sensor could not be initialized!')

