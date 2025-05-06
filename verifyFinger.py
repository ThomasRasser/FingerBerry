import time
from pyfingerprint.pyfingerprint import PyFingerprint

try:
    # Initialize the sensor
    f = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)
    
    if f.verifyPassword():
        print('Successfully connected to the sensor!')
    else:
        print('The given fingerprint sensor password is wrong!')
        exit(1)
    
    # Turn off both LEDs to start
    f.setLED(False)
    time.sleep(0.5)
    
    # Turn on blue LED when ready for fingerprint
    f.setLED(True, color='blue')
    print('Waiting for finger...')
    
    # Wait for finger to be placed on sensor
    while not f.readImage():
        pass
    
    # Turn on both LEDs when finger detected
    f.setLED(True, color='purple')
    print('Reading fingerprint...')
    
    # Convert image and search for matches
    f.convertImage(0x01)
    result = f.searchTemplate()
    
    position = result[0]
    accuracy = result[1]
    
    if position >= 0:
        print(f'Found match! Template position #{position}')
        print(f'Accuracy score: {accuracy}')
        
        # Success - blink blue LED
        for _ in range(5):
            f.setLED(True, color='blue')
            time.sleep(0.2)
            f.setLED(False)
            time.sleep(0.2)
    else:
        print('No match found.')
        # No match - blink red LED
        for _ in range(3):
            f.setLED(True, color='red')
            time.sleep(0.3)
            f.setLED(False)
            time.sleep(0.3)
    
except Exception as e:
    print(f'Error: {e}')
    # Error - solid red LED
    try:
        f.setLED(True, color='red')
        time.sleep(2)
        f.setLED(False)
    except:
        pass
    exit(1)
