#!/usr/bin/python3
"""
R503 Fingerprint manager that uses pyfingerprint library with LED indicator support
"""

import time
from enum import Enum

from pyfingerprint.pyfingerprint import PyFingerprint

from .r503led import R503LED, LEDColor, LEDMode


class FingerStatus(Enum):
    """Status codes for fingerprint operations"""

    SUCCESS = 0
    ERROR = 1
    NO_FINGER = 2
    ALREADY_EXISTS = 3
    NOT_FOUND = 4


class R503Manager:
    """
    R503 fingerprint sensor manager that combines the pyfingerprint library
    with LED status indicators
    """

    def __init__(self, port="/dev/ttyS0", baudrate=57600, address=0xFFFFFFFF, password=0x00000000):
        """
        Initialize the fingerprint manager

        Args:
            port (str): Serial port path
            baudrate (int): Serial baudrate
            address (int): Sensor address (default: 0xFFFFFFFF)
            password (int): Sensor password (default: 0x00000000)
        """
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.password = password

        self.led = R503LED(port, baudrate)

        self.finger = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def connect(self):
        """Connect to the fingerprint sensor"""
        try:
            self.finger = PyFingerprint(self.port, self.baudrate, self.address, self.password)

            self.led.connect()

            # Check if sensor is ready
            if not self.finger.verifyPassword():
                raise ValueError("Sensor password verification failed!")

            # Indicate successful connection
            self.led.led_on(LEDColor.GREEN)
            time.sleep(0.5)
            self.led.led_off()

            return True

        except Exception as e:
            print(f"Connection error: {e}")
            self.led.led_on(LEDColor.RED)
            time.sleep(0.5)
            self.led.led_off()
            return False

    def disconnect(self):
        """Disconnect from the sensor"""
        if self.led:
            self.led.disconnect()

    def set_led_status(self, status):
        """
        Set LED color based on status

        Args:
            status (FingerStatus): Operation status
        """
        if status == FingerStatus.SUCCESS:
            self.led.led_on(LEDColor.GREEN)
        elif status == FingerStatus.NO_FINGER:
            self.led.led_blink(LEDColor.BLUE)
        elif status == FingerStatus.ALREADY_EXISTS:
            self.led.led_blink(LEDColor.PURPLE)
        elif status == FingerStatus.NOT_FOUND:
            self.led.led_blink(LEDColor.RED)
        else:  # ERROR
            self.led.led_on(LEDColor.RED)

    def wait_for_finger(self):
        """
        Wait until finger is placed on sensor

        Returns:
            bool: True if finger detected, False on error
        """
        if not self.finger:
            return False

        # Blink blue while waiting
        self.led.led_blink(LEDColor.BLUE)

        try:
            print("Waiting for finger...")

            # Loop until finger detected
            while not self.finger.readImage():
                pass

            # Finger detected - change LED to solid blue
            self.led.led_on(LEDColor.BLUE)

            return True

        except Exception as e:
            print(f"Error waiting for finger: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return False

    def wait_finger_removed(self):
        """
        Wait until finger is removed from sensor

        Returns:
            bool: True on success, False on error
        """
        if not self.finger:
            return False

        # Purple blinking for "remove finger"
        self.led.led_blink(LEDColor.PURPLE)

        try:
            print("Remove finger...")

            # Wait until no finger detected
            while self.finger.readImage():
                pass

            # Finger removed
            self.led.led_off()
            time.sleep(0.5)

            return True

        except Exception as e:
            print(f"Error waiting for finger removal: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return False

    def enroll_finger(self):
        """
        Enroll a new fingerprint with LED status indicators

        Returns:
            tuple: (success, position or None)
        """
        if not self.finger:
            return False, None

        try:
            # Get the next available position
            position = self.finger.getTemplateCount()
            print(f"Currently used templates: {position}")

            if position >= self.finger.getStorageCapacity():
                print("Sensor database is full!")
                self.set_led_status(FingerStatus.ERROR)
                return False, None

            # First scan
            print("First scan - place finger on sensor")
            if not self.wait_for_finger():
                return False, None

            # Convert image and store in position 1
            self.finger.convertImage(0x01)

            # Wait for finger removal
            if not self.wait_finger_removed():
                return False, None

            # Second scan
            print("Second scan - place same finger again")
            if not self.wait_for_finger():
                return False, None

            # Convert image and store in position 2
            self.finger.convertImage(0x02)

            # Check if fingerprint already exists
            result = self.finger.searchTemplate()
            position_number = result[0]

            if position_number >= 0:
                print(f"Fingerprint already exists at position {position_number}!")
                self.set_led_status(FingerStatus.ALREADY_EXISTS)
                self.wait_finger_removed()
                return False, position_number

            # Create template
            self.finger.createTemplate()

            # Store template at new position
            self.finger.storeTemplate(position)

            print(f"Fingerprint enrolled successfully at position {position}!")
            self.set_led_status(FingerStatus.SUCCESS)
            time.sleep(1)
            self.led.led_off()

            self.wait_finger_removed()
            return True, position

        except Exception as e:
            print(f"Enrollment error: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return False, None

    def verify_finger(self):
        """
        Verify a fingerprint against the database

        Returns:
            tuple: (success, position, accuracy or None, None)
        """
        if not self.finger:
            return False, None, None

        try:
            # Wait for finger
            if not self.wait_for_finger():
                return False, None, None

            # Convert image
            self.finger.convertImage(0x01)

            # Search template
            result = self.finger.searchTemplate()
            position = result[0]
            accuracy = result[1]

            if position >= 0:
                print(f"Fingerprint found at position {position} with accuracy {accuracy}!")
                self.set_led_status(FingerStatus.SUCCESS)
                time.sleep(1)
                self.led.led_off()

                self.wait_finger_removed()
                return True, position, accuracy
            else:
                print("Fingerprint not found!")
                self.set_led_status(FingerStatus.NOT_FOUND)
                time.sleep(1)
                self.led.led_off()

                self.wait_finger_removed()
                return False, None, None

        except Exception as e:
            print(f"Verification error: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return False, None, None

    def delete_finger(self, position=None):
        """
        Delete a fingerprint from the database

        Args:
            position (int): Position to delete, or None to verify first

        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.finger:
            return False

        try:
            # If no position specified, verify finger first
            if position is None:
                print("Place finger to delete...")
                success, position, _ = self.verify_finger()

                if not success:
                    print("Fingerprint not found in database")
                    return False

            # Delete the template
            if self.finger.deleteTemplate(position):
                print(f"Fingerprint at position {position} deleted successfully!")
                self.set_led_status(FingerStatus.SUCCESS)
                time.sleep(1)
                self.led.led_off()
                return True
            else:
                print(f"Failed to delete fingerprint at position {position}")
                self.set_led_status(FingerStatus.ERROR)
                return False

        except Exception as e:
            print(f"Deletion error: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return False

    def get_template_count(self):
        """
        Get number of stored templates

        Returns:
            int: Number of templates or None on error
        """
        if not self.finger:
            return None

        try:
            count = self.finger.getTemplateCount()
            return count
        except Exception as e:
            print(f"Template count error: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return None

    def clear_database(self):
        """
        Clear all fingerprints from the database

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.finger:
            return False

        try:
            # Clear the database
            self.finger.clearDatabase()
            print("Database cleared successfully!")
            self.set_led_status(FingerStatus.SUCCESS)
            time.sleep(1)
            self.led.led_off()
            return True
        except Exception as e:
            print(f"Database clear error: {e}")
            self.set_led_status(FingerStatus.ERROR)
            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="R503 Fingerprint operations with LED feedback")
    parser.add_argument("--port", default="/dev/ttyS0", help="Serial port (default: /dev/ttyS0)")
    parser.add_argument("--baudrate", type=int, default=57600, help="Baudrate (default: 57600)")
    parser.add_argument(
        "--operation",
        choices=["enroll", "verify", "delete", "count", "clear"],
        required=True,
        help="Operation to perform",
    )
    parser.add_argument("--position", type=int, help="Position for deletion (0-199)")

    args = parser.parse_args()

    try:
        with R503Manager(args.port, args.baudrate) as manager:
            print(f"Connected to fingerprint sensor on {args.port}")

            if args.operation == "enroll":
                manager.enroll_finger()
            elif args.operation == "verify":
                manager.verify_finger()
            elif args.operation == "delete":
                manager.delete_finger(args.position)
            elif args.operation == "count":
                count = manager.get_template_count()
                print(f"Number of stored fingerprints: {count}")
            elif args.operation == "clear":
                confirm = input("This will delete ALL fingerprints. Type 'yes' to confirm: ")
                if confirm.lower() == "yes":
                    manager.clear_database()
                else:
                    print("Operation cancelled")
    except Exception as e:
        print(f"Error: {e}")
